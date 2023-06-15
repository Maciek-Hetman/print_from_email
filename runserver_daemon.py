from django.core.management import execute_from_command_line
from threading import Thread
import logging, time, cups, os, socket, email, imaplib, json, requests

def print_file(connection, printer, file_path: str = "/home/maciek/Pobrane/test.html", logger: logging.Logger = logging.getLogger(__name__)):
    try:
        logger.info('Printing file %s on printer %s' % (file_path, printer))
        connection.printFile(printer, file_path, file_path.split("/")[-1], {})
    except cups.IPPError:
        logger.error('File %s could not be printed on printer %s' % (file_path, printer))

def update_printers(cups_connection, api_url, logger):
    printers_scanned = list(cups_connection.getPrinters().keys())
    printers_api = requests.get(api_url).json()

    printer_api_keys = []
    if len(printers_api) > 0:
        for i in range(0, len(printers_api)):
            if printers_api[i]['printer_key'] not in printers_scanned:
                logger.info('Printer %s is no longer available, deleting' % printers_api[i]['printer_key'])
                requests.delete(api_url+f'/{i+1}/', data={'printer_key': printers_api[i]['printer_key']})
            else:
                printer_api_keys.append(printers_api[i]['printer_key'])

    for i in range(0, len(printers_scanned)):
        if printers_scanned[i] not in printer_api_keys:
            logger.info('New printer %s detected' % printers_scanned[i])
            requests.post(api_url, data={'printer_key': printers_scanned[i], 'enabled': False})

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
            logger.error('No printers available')
            os.exit(1)
    


def daemon(ip_address, logger: logging.Logger = logging.getLogger(__name__)):
    # Initial sleep to wait for django server to start
    time.sleep(10)

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
            logger.error('Config file is missing some values')
            os.exit(1)
    
    logger.info('Daemon config: %s' % config)

    cups_connection = cups.Connection()
    current_printer = update_printers(cups_connection, printer_api_url, logger)
    logger.info('Current printer: %s' % current_printer)


    while True:
        time.sleep(update_interval)

        whitelist_response = requests.get(whitelist_api_url)
        file_formats_response = requests.get(file_formats_api_url)

        if whitelist_response.status_code == 200:
            email_whitelist = whitelist_response.json()
            logger.info("Whitelist: %s" % email_whitelist)
        else:
            logger.error("Error:", whitelist_response.status_code)
            os.exit(1)
        
        if file_formats_response.status_code == 200:
            file_formats = file_formats_response.json()
            logger.info("File formats: %s" % file_formats)
        else:
            logger.error("Error:", file_formats_response.status_code)
            os.exit(1)

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



def run_server():
    ip_address = socket.gethostbyname(socket.gethostname()) + ":8000"

    FORMAT = '%(asctime)-15s - %(levelname)s - %(message)s'
    logging.basicConfig(format=FORMAT, level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.info('Starting runserver daemon')

    thread = Thread(target=daemon, args=(ip_address, logger), daemon=True)
    logger.info('Starting daemon thread')
    thread.start()

    logger.info('Starting django server on ip: %s' % (ip_address))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
    execute_from_command_line(['manage.py', 'runserver', ip_address])

if __name__ == '__main__':
    run_server()