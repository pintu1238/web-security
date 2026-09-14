TITLES = {
    "privacy_policy": "Privacy Policy",
    "employment_agreement": "Employment Agreement",
    "nda": "Non-Disclosure Agreement",
    "incident_response": "Incident Response Plan",
}


def render_document(document_type, business_name, owner, address, effective_date):
    title = TITLES[document_type]
    intro = f"""{title}

DRAFT FOR PROFESSIONAL REVIEW
This working draft was prepared for {business_name}, located at {address}, with {owner} as the responsible owner or representative. It takes effect on {effective_date} after appropriate legal and operational review. Adapt it to the business's actual practices and applicable law before use.
"""
    bodies = {
        "privacy_policy": """
1. Purpose and scope
This policy explains how the business handles personal information received from customers, workers, suppliers, website visitors, and other contacts.

2. Information collected
The business should list the contact, account, transaction, employment, device, and support information it actually collects and identify the reason for each collection.

3. Use, sharing, and retention
Use personal information only for stated business purposes. Record the service providers and public authorities with whom information may be shared. Keep information only as long as needed for the stated purpose, legal duties, dispute handling, or security.

4. Security and individual requests
Limit access, use reasonable administrative and technical safeguards, and provide a contact route for correction, access, deletion, or complaint requests where applicable.

5. Contact and updates
Questions should be directed to the business representative named above. Record material policy changes and their effective date.
""",
        "employment_agreement": """
1. Parties and role
Identify the employer and worker, job title, reporting line, place of work, start date, and whether the role is fixed-term or ongoing.

2. Pay, hours, and leave
State compensation, payment cycle, normal hours, overtime approval, benefits, leave, expenses, and required deductions in terms reviewed for applicable employment law.

3. Duties and workplace rules
Describe core duties, performance expectations, acceptable use of business systems, safety responsibilities, and policies incorporated into the agreement.

4. Confidentiality, records, and property
Protect legitimate confidential information, explain ownership and return of business property, and define permitted handling of staff and customer data.

5. Changes and ending employment
Document notice, handover, final payment, return of property, and dispute handling terms after local legal review.
""",
        "nda": """
1. Purpose
The parties may exchange confidential information only to evaluate or carry out their stated business relationship.

2. Confidential information
Define the business, technical, customer, pricing, security, and operational information covered. Exclude information already public, independently developed, lawfully received, or already known without restriction.

3. Recipient duties
Use the information only for the stated purpose, limit access to people who need it, apply reasonable safeguards, and notify the discloser of suspected unauthorized access.

4. Required disclosure and return
Allow disclosure required by law with advance notice where lawful. On request, return or securely destroy information, subject to documented legal retention needs.

5. Duration and remedies
Specify a reasonable confidentiality period, governing law, dispute process, and available remedies after professional review.
""",
        "incident_response": """
1. Activation and roles
Activate this plan when an event may threaten business systems, personal data, operations, or customers. Name an incident lead, technical lead, communications contact, and decision-maker with backups.

2. Triage and containment
Record when and how the event was found, affected systems, evidence, business impact, and immediate containment steps. Preserve logs and avoid destroying evidence.

3. Assessment and communication
Assess affected data, people, suppliers, and services. Obtain legal guidance on regulatory, contractual, law-enforcement, insurer, worker, and customer notifications. Communicate verified facts and keep a decision log.

4. Recovery
Remove the cause, restore from trusted backups, test critical services, monitor for recurrence, and authorize return to normal operations.

5. Review
Within a defined period, document the timeline, root causes, costs, lessons, and assigned corrective actions. Test and update this plan regularly.
""",
    }
    return title, intro + bodies[document_type].strip() + "\n"
