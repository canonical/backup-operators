---
myst:
  html_meta:
    "description lang=en": "A collection of charms for backup charms in machine environments."
---

<!-- vale Canonical.007-Headings-sentence-case = NO -->

# Backup Operators

<!-- vale Canonical.007-Headings-sentence-case = YES -->

Backup operators are a collection of [charms](https://documentation.ubuntu.com/juju/3.6/reference/charm/) that provide a highly integrated, low-operations backup solution for charms running in machine environments.

Backup operators deliver file-level backups using the tried-and-true Bacula system and leverage the `backup` relation to automatically define what and how to back up for all supported backup target charms in the Juju ecosystem. This significantly reduces the operational cost of setting up backups in complex systems.

For Site Reliability Engineers, backup operators offer a turnkey, out-of-the-box backup solution.

## In this documentation

|                                                                                                               |                                                                                                       |
|---------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------|
| [Tutorials](./tutorial.md)</br>  Get started - a hands-on introduction to using the charm for new users </br> | [How-to guides](./how-to/index.md) </br> Step-by-step guides covering key operations and common tasks |
| [Reference](./reference/index.md) </br> Technical information - specifications, APIs, architecture            | [Explanation](./explanation/index.md) </br> Concepts - discussion and clarification of key topics     |

## Contributing to this documentation

Documentation is an important part of this project, and we take the same open-source approach
to the documentation as the code. As such, we welcome community contributions, suggestions, and
constructive feedback on our documentation.
See [How to contribute](./how-to/contribution.md) for more information.


If there's a particular area of documentation that you'd like to see that's missing, please 
[file a bug](https://github.com/canonical/backup-operators/issues).

## Project and community

The backup operators are a member of the Ubuntu family. It's an open-source project that warmly welcomes community 
projects, contributions, suggestions, fixes, and constructive feedback.

- [Code of conduct](https://ubuntu.com/community/code-of-conduct)
- [Get support](https://discourse.charmhub.io/)
- [Join our online chat](https://matrix.to/#/#charmhub-charmdev:ubuntu.com)
- [Contribute](https://github.com/canonical/backup-operators/blob/main/CONTRIBUTING.md)

Thinking about using the backup operators for your next project? 
[Get in touch](https://matrix.to/#/#charmhub-charmdev:ubuntu.com)!

```{toctree}
:hidden:
:maxdepth: 1

Tutorial <tutorial>
how-to/index
reference/index
explanation/index
changelog
```
