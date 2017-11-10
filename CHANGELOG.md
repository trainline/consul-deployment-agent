# Changelog

All notable changes to this project will be documented in this file. The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/).
This project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [2.1.9] 2017-11-10

### Fixed

- Added missing EM_SERVICE_NAME environment variable for application stop lifecycle scripts

## [2.1.8] 2017-11-08

### Changed

- Only the two most recent deployment directories are retained. Issue [PD-736]. Pull request [#51].

### Fixed

- No output returned when a script does not complete before its timeout. Issue [PLATFORM-5863]. Pull request [#39].

## [2.1.7] 2017-11-02

### Changed
- Updated Readme

### Fixed
- Healthcheck default value

## [2.1.6] 2017-09-21

### Fixed
- Sensu health checks are not alerted during long deployments

## [2.1.5] 2017-09-18

### Fixed
- Unable to copy the contents of multiple directories to one target directory using the `files` section of `appspec.yaml`.

## [2.1.3] 2017-09-15

### Fixed
- sensu healthcheck registration tests

## [2.1.2] 2017-09-15

### Fixed
- Notification email check setting

## [2.1.1] 2017-09-12

### Fixed
- "No such file or directory" error when copying files during application installation.
- No port number selected for non blue/green deployments.

[Unreleased]: https://github.com/trainline/consul-deployment-agent/compare/2.1.9...HEAD
[2.1.9]: https://github.com/trainline/consul-deployment-agent/compare/2.1.8...2.1.9
[2.1.8]: https://github.com/trainline/consul-deployment-agent/compare/2.1.7...2.1.8
[2.1.7]: https://github.com/trainline/consul-deployment-agent/compare/2.1.6...2.1.7
[2.1.6]: https://github.com/trainline/consul-deployment-agent/compare/2.1.5...2.1.6
[2.1.5]: https://github.com/trainline/consul-deployment-agent/compare/2.1.4...2.1.5
[2.1.4]: https://github.com/trainline/consul-deployment-agent/compare/2.1.3...2.1.4
[2.1.3]: https://github.com/trainline/consul-deployment-agent/compare/2.1.2...2.1.3
[2.1.2]: https://github.com/trainline/consul-deployment-agent/compare/2.1.1...2.1.2
[2.1.1]: https://github.com/trainline/consul-deployment-agent/compare/2.1.0...2.1.1

[#51]: https://github.com/trainline/consul-deployment-agent/pull/51
[#39]: https://github.com/trainline/consul-deployment-agent/pull/39

[PLATFORM-5863]: https://jira.thetrainline.com/browse/PLATFORM-5863
[PD-736]: https://jira.thetrainline.com/browse/PD-736
