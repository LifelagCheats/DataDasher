<div align="center">

<img src="https://github.com/LifelagCheats/DataDasher/blob/main/Assets/DataDasherLogo.png" alt="Logo" width="200"/>

# DataDasher


![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)
![Maintained](https://img.shields.io/badge/maintained-No-red)
![GitHub contributors](https://img.shields.io/github/contributors/LifelagCheats/DataDasher)
![GitHub code size in bytes](https://img.shields.io/github/languages/code-size/LifelagCheats/DataDasher)
![GitHub forks](https://img.shields.io/github/forks/LifelagCheats/DataDasher?logoColor=ffff&color=%23ff0000)
![GitHub Repo stars](https://img.shields.io/github/stars/LifelagCheats/DataDasher?color=%2332cd32)

<img src="https://github.com/LifelagCheats/DataDasher/blob/main/Assets/preview.webp" alt="preview" width="800"/>


DataDasher is an "ethical" DDoS hacking tool designed for penetration testers and security professionals. It provides a suite of features to assess the security posture of web applications and networks in a legal and ethical manner.

</div>



## Table of Contents 
- #### [Features](#features)  
- #### [Installation](#installation)
- #### [Usage](#usage)
- #### [Upcoming features](#upcoming-features)  
- #### [Contribution Guidelines](#contribution-guidelines)


## Features

Datadasher offers various features, such as:

- **Statistics viewing**: View the number of packets sent and failed to sent, Ideal for those looking to enhance their website security and see how well they're protected.
- **Send Attacks**: DataDasher offers a variety of send attacks, such as HTTP GET attacks, UDP and TCP, for HTTP GET attacks, the port **does not need** to be specified, as the tool can already find it, althought for UDP and TCP attacks you do need to specify the port
- **SLOWLORIS AND SYN FLOODS**: DataDasher also offers two types of attacks, SLOWLORIS and SYN floods, as always, you need to specify the port, and options if you need/want to.
- **VARIETY AND OPTIONS**: You can also customize the options of attack in DataDasher, for example, you can customize amount or requests, packets or payload sent, and talking about payload, you can also customize it, and the rate is not something to forget.


## Installation

**Prerequisites**
Python 3.8 or higher
Git (for installation)

```bash
git clone https://github.com/LifelagCheats/DataDasher
cd DataDasher
pip install -r requirements.txt
python DataDasher.py
```
### Tested Operating Systems
<table>
    <tr>
        <th>Operative system</th>
        <th> Version </th>
    </tr>
    <tr>
        <td>Windows</td>
        <td>11/10</td>
    </tr>
    <tr>
        <td>Linux</td>
        <td>Arch, Debian, Ubuntu</td>
    </tr>
<table>

> [!WARNING]
> Anything below the specified OS version is not guaranteed to work and it's not going to be fixed 

## Usage

DataDasher offers two execution modes

### 1. Interactive TUI Mode
Launch without arguments for a guided experience:

```bash
python DataDasher.py
```

### 2. CLI Mode

Execute specific commands directly:
```bash
python DataDasher.py [attack_type] [attack_option] [target] [port] [parameters]
```

**Example commands:**

```bash
# HTTP GET test
python DataDasher.py send http example.com

# UDP test with custom port
python DataDasher.py send udp example.com 80 --count 1000
```

## Upcoming features
Here are some features that are planned for future implementation:

- [ ] Add new Attack modes
- [x] integrate WHOIS lookups

> [!NOTE]
> ### Some features are not implemented and are yet to be done


## Contribution Guidelines
Contributions are welcome! If you’re interested in helping improve DataDasher, please consider the following:
- Check the issues tab for current tasks.
- Fork the repository and create a pull request.
- Share your feedback and suggestions.

**for more information visit the [Contribution Guidelines](https://github.com/LifelagCheats/DataDasher/blob/main/CONTRIBUTING.md)**

Your support is greatly appreciated, as I am a solo developer and still learning. Thank you!
If you want to contact me, dm `@mylifeislag` by discord.


## Contributors
(thanks to all of you!)
<div align="center">
  <a href="https://github.com/LifelagCheats/DataDasher/graphs/contributors">
    <img src="https://contrib.rocks/image?repo=LifelagCheats/DataDasher" />
  </a>
</div>

## Star history

[![Star History Chart](https://api.star-history.com/svg?repos=LifelagCheats/DataDasher&type=Date)](https://star-history.com/#LifelagCheats/DataDasher&Date)



