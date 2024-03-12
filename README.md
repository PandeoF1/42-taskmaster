<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://github.com/github_username/repo_name">
    <img src="images/logo.png" alt="Logo" width="80" height="80">
  </a>

<h3 align="center">42 - Taskmaster</h3>

  <p align="center">
    Services management and monitoring tool
  </p>
</div>


## About The Project

Taskmaster is a job control manager project for 42 school.
It allows its users to control a number of processes on operating systems.

Inspired by the [Supervisor](https://github.com/Supervisor/supervisor)

### Prerequisites

Create a virtual environment using the following command:

* venv
  ```sh
  python3 -m venv venv && source venv/bin/activate
  ```

* pipenv
  ```sh 
  pip install -r requirements.txt
  ```

or use the devcontainer provided in the repository.

### Dependencies

* [Python](https://www.python.org/)
* [Cerberus](https://docs.python-cerberus.org/) # Provides data validation
* [PyYAML](https://pypi.org/project/PyYAML/) # Provides YAML parsing and dumping

## Installation

* From pypi
  ```sh
  pip install 42-taskmaster
  ```

* From source
  ```sh
  pip install .
  ```

## Usage

* Without arguments
    ```sh
    taskmaster
    ```
* With arguments
    ```sh
    taskmaster -f /path/to/config.yml
    ```


## Configuration file

```yaml
services:
  - name: sleep
    cmd: "sleep 100"
    numprocs: 8 # min 1 max 32
    umask: 077
    workingdir: /tmp
    autostart: true
    autorestart: unexpected # always, never unexpected
    exitcodes:
      - 0
      - 2
    startretries: 3
    starttime: 5
    stopsignal: USR1
    stoptime: 10
    stdout: ./taskmaster.yml # Optionnal (if not present don't log)
    stderr: /workspaces/42-taskmaster/logs/taskmaster.log # Optionnal
    # user: aaaaa # Optionnal (Downgrade privileges)
```


<!-- CONTRIBUTING -->
## Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".
Don't forget to give the project a star! Thanks again!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request



## Contributors

Nard Théo - GUI / Configuration

Lafay Timothée - Services management

