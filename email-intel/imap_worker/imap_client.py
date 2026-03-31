import imaplib


class IMAPClient:
    def __init__(self, account):
        self.host = account.host
        self.username = account.username
        self.password = account.get_password()
        self.last_uid = account.last_uid

    def fetch_new(self):
        imap = imaplib.IMAP4_SSL(self.host)
        try:
            imap.login(self.username, self.password)
            imap.select("INBOX")

            _, data = imap.uid("search", "UTF-8", f"UID {self.last_uid + 1}:*")
            uids = data[0].split() if data and data[0] else []

            messages = []
            for uid in uids:
                _, msg_data = imap.uid("fetch", uid, "(RFC822)")
                if not msg_data or not msg_data[0]:
                    continue
                raw = msg_data[0][1]
                if raw:
                    messages.append((int(uid), raw))

            if uids:
                self.last_uid = int(uids[-1])

            return messages
        finally:
            try:
                imap.close()
            except Exception:
                pass
            imap.logout()
