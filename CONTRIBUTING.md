# How to contribute to a Solace Project

We'd love for you to contribute and welcome your help. Here are some guidelines to follow:

- [Issues and Bugs](#issue)
- [Submitting a fix](#submitting)
- [Feature Requests](#features)
- [Questions](#questions)

## <a name="issue"></a> Did you find a issue?

- **Ensure the bug was not already reported** by searching on GitHub under [Issues](https://github.com/SolaceProducts/pubsubplus-kubernetes-quickstart/issues).

- If you're unable to find an open issue addressing the problem, [open a new one](https://github.com/SolaceProducts/pubsubplus-kubernetes-quickstart/issues). Be sure to include a **title and clear description**, as much relevant information as possible, and a **code sample** or an **executable test case** demonstrating the expected behavior that is not occurring.

## <a name="submitting"></a> Did you write a patch that fixes a bug?

Open a new GitHub pull request with the patch following the steps outlined below. Ensure the PR description clearly describes the problem and solution. Include the relevant issue number if applicable.

Before you submit your pull request consider the following guidelines:

- Search [GitHub](/https://github.com/SolaceProducts/pubsubplus-kubernetes-quickstart/pulls) for an open or closed Pull Request
  that relates to your submission. You don't want to duplicate effort.

### Submitting a Pull Request

Please follow these steps for all pull requests. These steps are derived from the [GitHub flow](https://help.github.com/articles/github-flow/).

#### Step 1: Fork

Fork the project and clone your fork
locally.

```sh
prompt:~$ git clone https://github.com/SolaceProducts/pubsubplus-kubernetes-quickstart
```

#### Step 2: Branch

Make your changes on a new git branch in your fork of the repository.

```sh
prompt:~$ git checkout -b my-fix-branch master
```

#### Step 3: Commit

Commit your changes using a descriptive commit message.

```sh
prompt:~$ git commit -a -m "Your Commit Message"
```

Note: the optional commit `-a` command line option will automatically "add" and "rm" edited files.

#### Step 4a: Rebase (if you have not yet pushed your branch to origin, else goto step 4b.)

Assuming you have not yet pushed your branch to origin, use `git rebase` (not `git merge`) to synchronize your work with the main
repository.

If you have not set the upstream, do so as follows:

```sh
prompt:~$ git remote add upstream https://github.com/SolaceProducts/pubsubplus-kubernetes-quickstart
```

then:

```sh
prompt:~$ git fetch upstream
prompt:~$ git rebase upstream/master
```

#### Step 4b: Merge (if you have already pushed our branch to origin)

Assuming you have already pushed your branch to origin, use `git merge` (not `git rebase`) to synchronize your work with the main
repository.

First ensure there are not any changes to master that you need to pick up, then merge in your changes.
You may need to resolve any conflicts on either of the merge steps.

```sh
prompt:~$ git merge master
prompt:~$ git checkout master
prompt:~$ git merge my-fix-branch
```


#### Step 5: Push

Push your branch to your fork in GitHub:

```sh
prompt:~$ git push origin my-fix-branch
```

#### Step 6: Pull Request

In GitHub, send a pull request to `solace-samples-semp:master`.

When fixing an existing issue, use the [commit message keywords](https://help.github.com/articles/closing-issues-via-commit-messages/) to close the associated GitHub issue.

- If we suggest changes then:
  - Make the required updates.
  - Commit these changes to your branch (ex: my-fix-branch)

That's it! Thank you for your contribution!

## <a name="features"></a> **Do you have an ideas for a new feature or a change to an existing one?**

- Open a GitHub [enhancement request issue](https://github.com/SolaceProducts/pubsubplus-kubernetes-quickstart/issues) and describe the new functionality.

##  <a name="questions"></a> Do you have questions about the source code?

- Ask any question about the code or how to use Solace messaging in the [Solace community](http://dev.solace.com/community/).
