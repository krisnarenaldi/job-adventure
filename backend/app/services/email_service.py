from typing import Optional
from datetime import datetime
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib


class EmailService:
    """Service for sending emails"""
    
    def __init__(self):
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.from_email = os.getenv("FROM_EMAIL", self.smtp_user)
        self.from_name = os.getenv("FROM_NAME", "Job Matching Platform")
    
    def _send_email(self, to_email: str, subject: str, html_content: str, text_content: Optional[str] = None):
        """Send an email using SMTP"""
        if not self.smtp_user or not self.smtp_password:
            print(f"Email service not configured. Would send email to {to_email} with subject: {subject}")
            return
        
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{self.from_name} <{self.from_email}>"
        msg['To'] = to_email
        
        # Add text and HTML parts
        if text_content:
            part1 = MIMEText(text_content, 'plain')
            msg.attach(part1)
        
        part2 = MIMEText(html_content, 'html')
        msg.attach(part2)
        
        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
        except Exception as e:
            print(f"Failed to send email: {str(e)}")
            raise
    
    def send_interview_invitation(
        self,
        candidate_email: str,
        candidate_name: str,
        job_title: str,
        company_name: str,
        interview_time: datetime,
        interview_type: str,
        meeting_link: Optional[str] = None,
        location: Optional[str] = None,
        notes: Optional[str] = None
    ):
        """Send interview invitation email"""
        
        # Format the interview time
        formatted_time = interview_time.strftime("%A, %B %d, %Y at %I:%M %p")
        
        # Build the email content
        subject = f"Interview Invitation: {job_title} at {company_name}"
        
        # Text version
        text_content = f"""
Dear {candidate_name},

We are pleased to invite you for an interview for the position of {job_title} at {company_name}.

Interview Details:
- Date & Time: {formatted_time}
- Type: {interview_type.title()}
"""
        
        if meeting_link:
            text_content += f"- Meeting Link: {meeting_link}\n"
        
        if location:
            text_content += f"- Location: {location}\n"
        
        if notes:
            text_content += f"\nAdditional Notes:\n{notes}\n"
        
        text_content += """
Please confirm your attendance by replying to this email.

We look forward to speaking with you!

Best regards,
The Hiring Team
"""
        
        # HTML version
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #4F46E5; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; background-color: #f9fafb; }}
        .details {{ background-color: white; padding: 15px; margin: 20px 0; border-left: 4px solid #4F46E5; }}
        .button {{ display: inline-block; padding: 12px 24px; background-color: #4F46E5; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
        .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Interview Invitation</h1>
        </div>
        <div class="content">
            <p>Dear {candidate_name},</p>
            <p>We are pleased to invite you for an interview for the position of <strong>{job_title}</strong> at <strong>{company_name}</strong>.</p>
            
            <div class="details">
                <h3>Interview Details</h3>
                <p><strong>Date & Time:</strong> {formatted_time}</p>
                <p><strong>Type:</strong> {interview_type.title()}</p>
"""
        
        if meeting_link:
            html_content += f'<p><strong>Meeting Link:</strong> <a href="{meeting_link}">{meeting_link}</a></p>\n'
        
        if location:
            html_content += f'<p><strong>Location:</strong> {location}</p>\n'
        
        html_content += '</div>\n'
        
        if notes:
            html_content += f'<div class="details"><h3>Additional Notes</h3><p>{notes}</p></div>\n'
        
        if meeting_link:
            html_content += f'<p style="text-align: center;"><a href="{meeting_link}" class="button">Join Interview</a></p>\n'
        
        html_content += """
            <p>Please confirm your attendance by replying to this email.</p>
            <p>We look forward to speaking with you!</p>
            <p>Best regards,<br>The Hiring Team</p>
        </div>
        <div class="footer">
            <p>This is an automated message from the Job Matching Platform.</p>
        </div>
    </div>
</body>
</html>
"""
        
        self._send_email(candidate_email, subject, html_content, text_content)
    
    def get_interview_invitation_preview(
        self,
        candidate_name: str,
        job_title: str,
        company_name: str,
        interview_time: datetime,
        interview_type: str,
        meeting_link: Optional[str] = None,
        location: Optional[str] = None,
        notes: Optional[str] = None
    ) -> dict:
        """Get a preview of the interview invitation email"""
        
        formatted_time = interview_time.strftime("%A, %B %d, %Y at %I:%M %p")
        
        subject = f"Interview Invitation: {job_title} at {company_name}"
        
        preview = {
            "subject": subject,
            "to": f"{candidate_name} <candidate@example.com>",
            "from": f"{self.from_name} <{self.from_email}>",
            "preview_text": f"Interview invitation for {job_title} on {formatted_time}",
            "details": {
                "job_title": job_title,
                "company_name": company_name,
                "interview_time": formatted_time,
                "interview_type": interview_type.title(),
                "meeting_link": meeting_link,
                "location": location,
                "notes": notes
            }
        }
        
        return preview
    
    async def send_shared_link_email(
        self,
        recipient_email: str,
        sender_name: str,
        job_title: str,
        share_url: str,
        custom_message: Optional[str] = None
    ):
        """Send shared link email to hiring manager or stakeholder"""
        
        subject = f"{sender_name} shared candidate rankings for {job_title}"
        
        # Text version
        text_content = f"""
Hello,

{sender_name} has shared candidate rankings with you for the position: {job_title}

"""
        
        if custom_message:
            text_content += f"Message from {sender_name}:\n{custom_message}\n\n"
        
        text_content += f"""
View the candidates here: {share_url}

This link provides view-only access to the candidate rankings and match analysis.

Best regards,
Job Matching Platform
"""
        
        # HTML version
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #4F46E5; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; background-color: #f9fafb; }}
        .message-box {{ background-color: white; padding: 15px; margin: 20px 0; border-left: 4px solid #4F46E5; }}
        .button {{ display: inline-block; padding: 12px 24px; background-color: #4F46E5; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
        .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Candidate Rankings Shared</h1>
        </div>
        <div class="content">
            <p>Hello,</p>
            <p><strong>{sender_name}</strong> has shared candidate rankings with you for the position:</p>
            <h2 style="color: #4F46E5; margin: 10px 0;">{job_title}</h2>
"""
        
        if custom_message:
            html_content += f"""
            <div class="message-box">
                <h3>Message from {sender_name}:</h3>
                <p>{custom_message}</p>
            </div>
"""
        
        html_content += f"""
            <p style="text-align: center;">
                <a href="{share_url}" class="button">View Candidates</a>
            </p>
            <p style="font-size: 14px; color: #666;">This link provides view-only access to the candidate rankings and match analysis.</p>
        </div>
        <div class="footer">
            <p>This is an automated message from the Job Matching Platform.</p>
        </div>
    </div>
</body>
</html>
"""
        
        self._send_email(recipient_email, subject, html_content, text_content)


# Singleton instance
email_service = EmailService()
