// solace-pod-modifier-admission-plugin
//
// Copyright 2021-2022 Solace Corporation. All rights reserved.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
// http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	jsonpatch "github.com/mattbaird/jsonpatch"
	"io/ioutil"
	admissionv1 "k8s.io/api/admission/v1"
	corev1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/apimachinery/pkg/runtime/serializer"
	"net/http"
)

var (
	runtimeScheme = runtime.NewScheme()
	codecs        = serializer.NewCodecFactory(runtimeScheme)
	deserializer  = codecs.UniversalDeserializer()
)

var ignoredNamespaces = []string{
	metav1.NamespaceSystem,
	metav1.NamespacePublic,
}

const (
	admissionWebhookAnnotationInjectKey = "pod-modifier-webhook.solace.com/inject"
	admissionWebhookAnnotationStatusKey = "pod-modifier-webhook.solace.com/status"
)

type WebhookServer struct {
	server *http.Server
}

// Webhook Server parameters
type WhSvrParameters struct {
	port     int    // webhook server port
	certFile string // path to the x509 certificate for https
	keyFile  string // path to the x509 private key matching `CertFile`
}

type patchOperation struct {
	Op    string      `json:"op"`
	Path  string      `json:"path"`
	Value interface{} `json:"value,omitempty"`
}

// Check whether the target resource need to be mutated
func mutationRequired(ignoredList []string, metadata *metav1.ObjectMeta) bool {
	// skip special kubernetes system namespaces
	for _, namespace := range ignoredList {
		if metadata.Namespace == namespace {
			infoLogger.Printf("Skip mutation for %v for it's in special namespace:%v", metadata.Name, metadata.Namespace)
			return false
		}
	}
	return true
}

// main mutation process
func (whsvr *WebhookServer) mutate(ar *admissionv1.AdmissionReview) *admissionv1.AdmissionResponse {
	req := ar.Request
	var pod corev1.Pod
	if err := json.Unmarshal(req.Object.Raw, &pod); err != nil {
		warningLogger.Printf("Could not unmarshal raw object: %v", err)
		return &admissionv1.AdmissionResponse{
			Result: &metav1.Status{
				Message: err.Error(),
			},
		}
	}

	infoLogger.Printf("AdmissionReview for Kind=%v, Namespace=%v Name=%v (%v) UID=%v patchOperation=%v UserInfo=%v",
		req.Kind, req.Namespace, req.Name, pod.Name, req.UID, req.Operation, req.UserInfo)

	// determine whether to perform mutation
	if !mutationRequired(ignoredNamespaces, &pod.ObjectMeta) {
		infoLogger.Printf("Skipping mutation for %s/%s due to policy check", pod.Namespace, pod.Name)
		return &admissionv1.AdmissionResponse{
			Allowed: true,
		}
	}

	// annotations := map[string]string{admissionWebhookAnnotationStatusKey: "injected"}
	// patchBytes, err := createPatch(&pod, annotations)
	patchBytes, err := createPatch(&pod)
	if err != nil {
		return &admissionv1.AdmissionResponse{
			Result: &metav1.Status{
				Message: err.Error(),
			},
		}
	}
	if bytes.Compare(patchBytes, []byte{}) == 0 {
		infoLogger.Printf("No change required, not providing a patch in AdmissionResponse")
		return &admissionv1.AdmissionResponse{
			Allowed: true,
		}
	}
	infoLogger.Printf("AdmissionResponse: patch=%v\n", string(patchBytes))
	return &admissionv1.AdmissionResponse{
		Allowed: true,
		Patch:   patchBytes,
		PatchType: func() *admissionv1.PatchType {
			pt := admissionv1.PatchTypeJSONPatch
			return &pt
		}(),
	}
}

func createPatch(pod *corev1.Pod) ([]byte, error) {
	infoLogger.Printf("Create patch for pod: %s/%s", pod.Name, pod.Namespace)

	initializedPod := pod.DeepCopy()

	a := pod.ObjectMeta.GetAnnotations()
	podDefinitionAnnotation, ok := a[annotation+".podDefinition"]

	if !ok {
		infoLogger.Printf("Required '%s' annotation missing; skipping pod", annotation+".podDefinition")
		return []byte{}, nil
	}

	var c config
	err := json.Unmarshal([]byte(podDefinitionAnnotation), &c)
	if err != nil {
		errorLogger.Printf("Unmarshal failed err %v  ,  Annotation %s", err, podDefinitionAnnotation)
		return []byte{}, err
	}

	var cpod corev1.Pod
	found := false
	for _, cpod = range c.Pods {
		if pod.ObjectMeta.Name == cpod.ObjectMeta.Name {
			found = true
			break
		}
	}

	if !found {
		infoLogger.Printf("Pod name is not matching annotation - skipping this pod.")
		return []byte{}, nil
	}

	// Modify the containers resources, if the container name of the specification matches
	// the container name of the "initialized pod container name"
	// Then patch the original pod
	found = false
	for _, configContainer := range cpod.Spec.Containers {
		for ii, initializedContainer := range initializedPod.Spec.Containers {
			if configContainer.Name == initializedContainer.Name {
				initializedPod.Spec.Containers[ii].Resources = configContainer.Resources
				found = true
			}
		}
	}
	if !found {
		infoLogger.Printf("No container name is matching annotation - skipping this pod.")
		return []byte{}, nil
	}

	oldData, err := json.Marshal(pod)
	if err != nil {
		errorLogger.Printf(err.Error())
		return []byte{}, err
	}

	newData, err := json.Marshal(initializedPod)
	if err != nil {
		errorLogger.Printf(err.Error())
		return []byte{}, err
	}
	patch, err := jsonpatch.CreatePatch(oldData, newData)
	if err != nil {
		errorLogger.Printf(err.Error())
		return []byte{}, err
	}

	patchBytes, err := json.Marshal(patch)
	if err != nil {
		errorLogger.Printf(err.Error())
		return []byte{}, err
	}

	return patchBytes, nil
}

// Serve method for webhook server
func (whsvr *WebhookServer) serve(w http.ResponseWriter, r *http.Request) {
	var body []byte
	if r.Body != nil {
		if data, err := ioutil.ReadAll(r.Body); err == nil {
			body = data
		}
	}
	if len(body) == 0 {
		warningLogger.Println("empty body")
		http.Error(w, "empty body", http.StatusBadRequest)
		return
	}

	// verify the content type is accurate
	contentType := r.Header.Get("Content-Type")
	if contentType != "application/json" {
		warningLogger.Printf("Content-Type=%s, expect application/json", contentType)
		http.Error(w, "invalid Content-Type, expect `application/json`", http.StatusUnsupportedMediaType)
		return
	}

	var admissionResponse *admissionv1.AdmissionResponse
	ar := admissionv1.AdmissionReview{}
	if _, _, err := deserializer.Decode(body, nil, &ar); err != nil {
		warningLogger.Printf("Can't decode body: %v", err)
		admissionResponse = &admissionv1.AdmissionResponse{
			Result: &metav1.Status{
				Message: err.Error(),
			},
		}
	} else {
		admissionResponse = whsvr.mutate(&ar)
	}

	admissionReview := admissionv1.AdmissionReview{
		TypeMeta: metav1.TypeMeta{
			APIVersion: "admission.k8s.io/v1",
			Kind:       "AdmissionReview",
		},
	}
	if admissionResponse != nil {
		admissionReview.Response = admissionResponse
		if ar.Request != nil {
			admissionReview.Response.UID = ar.Request.UID
		}
	}

	resp, err := json.Marshal(admissionReview)
	if err != nil {
		warningLogger.Printf("Can't encode response: %v", err)
		http.Error(w, fmt.Sprintf("could not encode response: %v", err), http.StatusInternalServerError)
	}
	infoLogger.Printf("Ready to write reponse ...")
	if _, err := w.Write(resp); err != nil {
		warningLogger.Printf("Can't write response: %v", err)
		http.Error(w, fmt.Sprintf("could not write response: %v", err), http.StatusInternalServerError)
	}
}
