# Portuguese Citizen Card Web Reader

A Python-based web application that allows reading data from Portuguese Citizen Cards (Cartão de Cidadão) using the official Autenticação.gov plugin.

Read more about this project and the technical details in my blog:
https://tragio.pt/articles/how-to-read-portuguese-citizen-cards-in-web-applications

## Features

- Read basic citizen information from the card
- Extract and convert photo from JP2 to JPEG format
- Secure communication with government authentication plugin
- Support for both local and cloud plugin endpoints

## Requirements

- Python 3.6 or higher
- Card Reader compatible with Portuguese Citizen Card
- Plugin Autenticação.gov installed and running
- Certificate .p12 file and password from Autenticação.gov

## Installation

1. Clone this repository:

```bash
git clone https://github.com/tragio/portuguese-citizen-card-web-reader.git
cd portuguese-citizen-card-web-reader
```

2. Install required Python packages:

```bash
pip install -r requirements.txt
```

3. Place your .p12 certificate in the certs directory

4. Update the certificate password in config.py

## Usage

1. Start the FastAPI server:

```bash
uvicorn main:app --reload --port 8000
```

2. Open your browser and go to http://127.0.0.1:8000/

3. Insert your Citizen Card in the reader

4. Click "Run Complete Chain" to read the card data

## Certificate

You need to ask [Autenticação.gov entity](https://www.autenticacao.gov.pt/web/guest/contactos) for the certificate, you will receive a certificate `.jks` file. You need to convert this file to a `.p12` file. You can use the following command to convert the `.jks` file to a `.p12` file:

Convert the certificate using this command:

```bash
keytool -importkeystore -srckeystore CERTIFICATE_NAME.jks -srcstoretype JKS -deststoretype PKCS12 -destkeystore gov_cert.p12
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

If you find this project useful and you are in the mood, feel free to offer me a coffee:

<a href="https://www.buymeacoffee.com/tragio" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 60px !important;width: 217px !important;" ></a>
