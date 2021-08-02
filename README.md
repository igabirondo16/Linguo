# Linguo

Linguo is a chatbot implemented with Rasa framework, to get the daily news in Basque. This project has been developed with the [IXA research group](http://ixa.si.ehu.es/) during a summer internship, and directed by [Gorka Azkune](https://gazkune.github.io/) and [Eneko Agirre](https://eagirre.github.io/).

## Installation

Linguo can be installed from GitHub.

```bash
git clone https://github.com/igabirondo16/Linguo.git
```

## Requirements

- Rasa
- Python 3
- Whoosh
- IxaPipes
- BeautifulSoup
- Requests
- Datetime

## Usage

First of all, retraining Rasa's model is recommended:

```bash
rasa train
```
After that, ngrok tunnel must be deployed. This step can also be done with [NgrokTunnelGenerator](https://github.com/igabirondo16/NgrokTunnelGenerator).

```bash
ngrok http 5005
```
Start Rasa action server:
```bash
rasa run actions
```
Finally, start Rasa server:
```bash
rasa run
```

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## Note

This is a demo version, so critical errors may be found. In case any bug is found, opening an issue would be appreciated.
