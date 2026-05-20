# POD Remove Button: Problem and Resolution

Problem (plain language):
- When staff click the "Remove POD" button (the control used to delete a Proof-of-Delivery image) inside the consignment information modal, nothing happens or an error is shown and the POD remains visible.

Why this matters:
- Staff need to be able to remove incorrect or duplicate POD images quickly. If removal doesn't work, records stay incorrect and require manual cleanup.

What was causing it (plain language):
- The page's remove button was sending a request to the server but the browser and server did not always exchange the right information. That meant the server sometimes rejected the request (for example if the session expired) or returned a login page instead of a success message, and the page did not show a clear error to the user.

What we changed (plain language):
- We fixed the button so it sends the request in a way the server expects and made the page show a clear success or error message. This makes the removal action reliable and gives staff feedback when something goes wrong.

What staff should do now:
- Try the "Remove POD" button again. If the POD disappears and you see a confirmation message, the issue is resolved.
- If it still fails, take note of the consignment number and the time, and include a screenshot of any message shown — then report it to the development team.

Follow-up / Contact:
- If this happens repeatedly, please report the consignment ID and a screenshot of the modal and the browser console (if possible). The development team will investigate further.

---

File: app/static/js/consignments.js (fix): added credentials and improved error handling for the POD delete request.
