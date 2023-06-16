from django.core.management import execute_from_command_line
from threading import Thread
from urllib.parse import quote
import logging, time, cups, os, sys, netifaces, email, imaplib, json, requests, datetime

class NoIPAddressFoundException(Exception):
    pass

def print_file(connection, printer, file_path: str = "/home/maciek/Pobrane/test.html", logger: logging.Logger = logging.getLogger(__name__)):
    try:
        logger.info('Printing file %s on printer %s' % (file_path, printer))
        connection.printFile(printer, file_path, file_path.split("/")[-1], {})
    except cups.IPPError:
        logger.error('File %s could not be printed on printer %s' % (file_path, printer))

def request(api_url, action, logger, data={}):
    try:
        if action == "get":
            return requests.get(api_url).json()
        elif action == "delete":
            requests.delete(api_url)
        elif action == "post":
            requests.post(api_url, data=data)
        else:
            logger.exception("Unknown action")
            raise
    except requests.exceptions.ConnectionError:
        logger.exception("Failed to connect to REST API")
        raise
    except requests.exceptions.InvalidURL:
        logger.exception("Invalid URL")
        raise
    except requests.exceptions.MissingSchema:
        logger.exception("Missing URL schema")
        raise
    except:
        logger.exception("Unknown error while connecting to REST API")
        raise
        
def update_printers(cups_connection, api_url, logger):
    try:
        printers_scanned = list(cups_connection.getPrinters().keys())
    except cups.IPPError as e:
        if e == cups.IPP_OPERATION_NOT_SUPPORTED:
            logger.exception("Not a CUPS server")
            raise

        logger.exception("CUPS server error")
        raise

    printers_api = request(api_url, "get", logger)

    printer_api_keys = []
    if len(printers_api) > 0:
        for printer in printers_api:
            if printer['printer_key'] not in printers_scanned:
                logger.info('Printer %s is no longer available, deleting' % printer['printer_key'])
                # requests.delete(api_url+f"{quote(printer['printer_key'])}/", data={'printer_key': printer})
                request(api_url+f"{quote(printer['printer_key'])}/", "delete", logger)
            else: 
                printer_api_keys.append(printer['printer_key'])

    for printer in printers_scanned:
        if printer not in printer_api_keys:
            logger.info('New printer %s detected' % printer)
            request(api_url, "post", {'printer_key': printer, 'enabled': False}, logger)

    enabled_printers = []
    for printer in requests.get(api_url).json():
        if printer['enabled']:
            enabled_printers.append(printer['printer_key'])
    
    try:
        logger.info("Enabled printer: %s" % enabled_printers[0])
        return enabled_printers[0]
    except IndexError:
        try:
            logger.warning("No printers enabled, using first printer")
            return printers_scanned[0]
        except IndexError:
            logger.exception('No printers available')
            raise
    


def daemon(ip_address, logger: logging.Logger = logging.getLogger(__name__)):
    # Wait for django server to start
    time.sleep(5)

    whitelist_api_url = f"http://{ip_address}/api/whitelist/"
    file_formats_api_url = f"http://{ip_address}/api/file_formats/"
    printer_api_url = f"http://{ip_address}/api/printers/"

    with open('config.json') as f:
        config = json.load(f)

        try:
            email_address = config['email']
            email_password = config['password']
            imap_server = config['imap']
            update_interval = config['update_interval']
            imap_port = config['imap_port']
            mailbox = config['mailbox']
        except KeyError:
            logger.exception('Config file is missing some values')
            raise
    
    logger.info('Daemon config: %s' % config)

    try:
        cups_connection = cups.Connection()
    except RuntimeError:
        logger.exception("Failed to connect to CUPS server")
        raise
    except cups.IPPError:
        logger.exception("CUPS server error")
        raise

    while True:
        time.sleep(update_interval)

        current_printer = update_printers(cups_connection, printer_api_url, logger)
        logger.info('Current printer: %s' % current_printer)

        whitelist_response = requests.get(whitelist_api_url)
        file_formats_response = requests.get(file_formats_api_url)

        if whitelist_response.status_code == 200:
            email_whitelist = whitelist_response.json()
            logger.info("Whitelist: %s" % email_whitelist)
        else:
            logger.exception("Error:", whitelist_response.status_code)
            raise
        
        if file_formats_response.status_code == 200:
            file_formats = file_formats_response.json()
            logger.info("File formats: %s" % file_formats)
        else:
            logger.exception("Error:", file_formats_response.status_code)
            raise

        imap = imaplib.IMAP4_SSL(imap_server, port=imap_port)
        imap.login(email_address, email_password)
        imap.select(mailbox)

        status, data = imap.search(None, 'UNSEEN')
        email_ids = data[0].split()

        for email_id in email_ids:
            status, data = imap.fetch(email_id, '(RFC822)')

            raw_email = data[0][1]
            msg = email.message_from_bytes(raw_email)
            sender_name, sender_email = email.utils.parseaddr(msg['From'])

            logger.info("New mail from %s with email %s" % (sender_name, sender_email))
            
            for email_dict in email_whitelist:
                if email_dict['email'] == sender_email:
                    for part in msg.walk():
                        if part.get_content_disposition() is not None:
                            filename = part.get_filename()
                            file_extension = filename.split('.')[-1]
                            logger.info('File %s with extension %s' % (filename, file_extension))

                            for file_format in file_formats:
                                if file_format['file_format'] == file_extension and file_format['enabled'] == True:
                                    working_dir = os.getcwd()

                                    save_path = os.path.join(working_dir, filename)

                                    with open(save_path, 'wb') as fp:
                                        logger.info('Saving file %s to %s' % (filename, save_path))
                                        fp.write(part.get_payload(decode=True))

                                    logger.info('Printing file %s' % filename)
                                    print_file(connection=cups_connection, printer=current_printer, logger=logger, file_path=save_path)
                                    logger.info('File %s printed successfully' % filename)

                                    time.sleep(10)
                                    
                                    logger.info('Removing file %s' % filename)
                                    os.remove(save_path)

                                    break

                    break
        
        imap.close()
        imap.logout()

def get_ip_address():
    interfaces = netifaces.interfaces()
    for interface in interfaces:
        addresses = netifaces.ifaddresses(interface)
        if netifaces.AF_INET in addresses:
            ip_address = addresses[netifaces.AF_INET][0]['addr']
            if ip_address.startswith("192"):
                return ip_address
    
    raise NoIPAddressFoundException("No IP address found")

def run_server():
    FORMAT = '%(asctime)-15s - %(levelname)s - %(message)s'

    logging.basicConfig(level=logging.INFO)
    
    file_handler = logging.FileHandler(f"{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log")
    file_handler.setLevel(logging.INFO)
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    formatter = logging.Formatter(FORMAT)
    
    file_handler.setFormatter(formatter)
    
    console_handler.setFormatter(formatter)
    
    logger = logging.getLogger(__name__)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    # ip_address = "192.168.1.100:8000"

    if 'ip_address' not in locals():
        try:
            ip_address = get_ip_address() + ":8000"
        except NoIPAddressFoundException as e:
            logger.warning("Cannot find IP address, please set it manually in runserver_daemon.py")
            logger.error('%s - exiting' % str(e))
            sys.exit(1)
    

    thread = Thread(target=daemon, args=(ip_address, logger), daemon=True)
    logger.info('Starting daemon thread')
    thread.start()

    logger.info('Starting django server on ip: %s' % (ip_address))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
    execute_from_command_line(['manage.py', 'runserver', ip_address])

if __name__ == '__main__':
    run_server()