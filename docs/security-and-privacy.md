# Orbit security and privacy FAQ

**Where is workspace data stored?** Orbit stores production workspace data in US East (Northern Virginia). Backups are encrypted and retained for 30 days. Business customers can request a data processing agreement from **security@orbit.example**.

**Is data encrypted?** Network traffic uses TLS 1.2 or newer. Stored workspace data and backups are encrypted at rest using AES-256. Access to production systems is limited to authorized operations staff and logged.

**Does Orbit train AI models on our content?** No. Orbit does not use customer workspace content to train public or shared AI models. Connected GitHub repositories sync issue metadata only; Orbit does not ingest repository source code.

**How do I export or delete workspace data?** Workspace owners can export projects and issues from **Settings → Data → Export** as a JSON archive. To permanently delete a workspace, use **Settings → General → Delete workspace**. Deletion is immediate for active data; encrypted backups expire within 30 days.

**How do I report a vulnerability?** Email **security@orbit.example** with steps to reproduce and an impact summary. Please do not include real customer data. Orbit acknowledges security reports within 2 business days.
