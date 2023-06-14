from django.core.management import execute_from_command_line
from threading import Thread
import logging, time, cups, os, socket, email, imaplib, json

def print_file(connection, printer, file_path: str = "/home/maciek/Pobrane/test.html", logger: logging.Logger = logging.getLogger(__name__), file_formats: list = ['html', 'pdf', 'jpg', 'jpeg', 'png']):
    if file_path.split('.')[-1] in file_formats:
        try:
            logger.info('Printing file %s on printer %s' % (file_path, printer))
            connection.printFile(printer, file_path, file_path.split("/")[-1], {})
        except cups.IPPError:
            logger.error('File %s could not be printed on printer %s' % (file_path, printer))
    else:
        logger.error('File %s has unsupported format' % file_path)

def daemon(logger: logging.Logger = logging.getLogger(__name__)):
    with open('config.json') as f:
        config = json.load(f)

        try:
            email_address = config['email']
            email_password = config['password']
            imap_server = config['imap']
            update_interval = config['update_interval']
            imap_port = config['imap_port']
        except KeyError:
            logger.error('Config file is missing some values')
            os.exit(1)
    
    logger.info('Daemon config: %s' % config)

    conn = cups.Connection()
    printers = list(conn.getPrinters().keys())
    logger.info('Available printers: %s' % printers)

    # Current printer config
    # For now default is first printer in list
    current_printer = printers[0]
    logger.info('Current printer: %s' % current_printer)

    while True:
        imap = imaplib.IMAP4_SSL(imap_server, port=imap_port)
        imap.login(email_address, email_password)
        mailbox = "INBOX"
        imap.select(mailbox)

        status, data = imap.search(None, 'UNSEEN')
        email_ids = data[0].split()

        for email_id in email_ids:
            status, data = imap.fetch(email_id, '(RFC822)')

            raw_email = data[0][1]
            msg = email.message_from_bytes(raw_email)

            for part in msg.walk():
                if part.get_content_disposition() is not None:
                    filename = part.get_filename()
                    save_path = os.path.join(os.getcwd(), filename)

                    with open(save_path, 'wb') as fp:
                        logger.info('Saving file %s to %s' % (filename, save_path))
                        fp.write(part.get_payload(decode=True))
        
        imap.close()
        imap.logout()

        print_file(connection=conn, printer=current_printer, logger=logger)
        time.sleep(update_interval)


def run_server():
    ip_address = socket.gethostbyname(socket.gethostname()) + ":8000"

    FORMAT = '%(asctime)-15s - %(levelname)s - %(message)s'
    logging.basicConfig(format=FORMAT, level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.info('Starting runserver daemon')

    thread = Thread(target=daemon, args=(logger,), daemon=True)
    logger.info('Starting daemon thread')
    thread.start()

    logger.info('Starting django server on ip: %s' % (ip_address))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
    execute_from_command_line(['manage.py', 'runserver', ip_address])

if __name__ == '__main__':
    run_server()