# Life Valley Content Review: one-time setup (signed in to Google as hello@alignd.in)

The review page stores every login, approval and comment in a Google Sheet that Alignd owns. This takes about 5 minutes, once.

## 1. Create the Sheet and the script
1. Go to sheets.new and name the new Sheet **Life Valley Content Reviews**.
2. Choose **Extensions → Apps Script**. Delete everything in the editor, paste in all of `Code.gs`, and click **Save**.
3. In the function list next to **Debug**, choose **setup** and click **Run**. Google asks for permission: click **Review permissions**, pick hello@alignd.in, then **Advanced → Go to project (unsafe) → Allow**. This creates the Users, Reviews, Activity and Config tabs.

## 2. Put it online
1. Click **Deploy → New deployment**. Next to "Select type", click the gear and choose **Web app**.
2. Set **Execute as: Me** and **Who has access: Anyone**. Click **Deploy**.
3. Copy the **Web app URL** (it starts with https://script.google.com/macros/s/) and send it to Claude. Claude connects the page and sends the keys to the Sheet itself.

## 3. Add people (any time)
In the **Users** tab, add one row per person: **email**, **name**, **active** = yes. Leave the other columns empty. They open the review page, choose "Set up your account" and pick their own password.

People with an @alignd.in or @lifevalley.in address can set themselves up without a row. Everyone else (a gmail address, Intersmart's developer) needs a row first.

- **Forgotten password:** clear their `pass_hash` cell. They choose a new one at next sign-in.
- **Remove access:** set `active` to `no`. Their login stops at once.
- **History:** **Activity** has every sign-in; **Reviews** has every approval, change request, comment and "Mark as live", with the quoted text.

## Updating the script later
Paste the new `Code.gs`, Save, then **Deploy → Manage deployments → pencil → Version: New version → Deploy**. The URL stays the same.

## What the script can and cannot do
- It reads and writes only this Sheet (`@OnlyCurrentDoc`): no other files, no email.
- Passwords are stored only as salted SHA-256 hashes. Logins last 6 hours. Five wrong passwords lock that email for 15 minutes.
