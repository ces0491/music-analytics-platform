# backend/services/email_service.py
import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.utils import formataddr
from typing import List, Dict, Optional
from datetime import datetime
import json
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

class EmailService:
    """Professional email service for music analytics reports"""
    
    def __init__(self):
        # Email configuration from environment
        self.smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.environ.get('SMTP_PORT', '587'))
        self.smtp_username = os.environ.get('SMTP_USERNAME', '')
        self.smtp_password = os.environ.get('SMTP_PASSWORD', '')
        self.from_email = os.environ.get('FROM_EMAIL', self.smtp_username)
        self.from_name = os.environ.get('FROM_NAME', 'Prism Analytics')
        
        # Email templates
        template_dir = Path(__file__).parent.parent / 'templates' / 'emails'
        self.jinja_env = Environment(loader=FileSystemLoader(str(template_dir)))
        
        # Brand colors for email styling
        self.brand_colors = {
            'primary': '#1A1A1A',
            'accent': '#E50914',
            'secondary': '#333333',
            'background': '#FFFFFF',
            'text': '#444444'
        }
    
    def send_wrapped_report(self, recipient_email: str, pdf_path: str, 
                           artist_name: str, year: int, 
                           additional_message: str = None) -> Dict:
        """Send Wrapped report via email"""
        try:
            subject = f"🎵 {artist_name} - Your {year} Music Wrapped Report"
            
            # Prepare email content
            email_data = {
                'artist_name': artist_name,
                'year': year,
                'report_type': 'Wrapped',
                'generated_date': datetime.now().strftime('%B %d, %Y'),
                'additional_message': additional_message,
                'brand_colors': self.brand_colors
            }
            
            # Generate HTML content
            html_content = self._render_wrapped_email_template(email_data)
            text_content = self._generate_text_version(email_data)
            
            # Send email with attachment
            return self._send_email_with_attachment(
                recipient_email=recipient_email,
                subject=subject,
                html_content=html_content,
                text_content=text_content,
                attachment_path=pdf_path,
                attachment_name=f"{artist_name}_Wrapped_{year}.pdf"
            )
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def send_monthly_report(self, recipient_email: str, pdf_path: str,
                           artist_name: str, period: str) -> Dict:
        """Send monthly report via email"""
        try:
            subject = f"📊 {artist_name} - Monthly Performance Report ({period})"
            
            email_data = {
                'artist_name': artist_name,
                'period': period,
                'report_type': 'Monthly',
                'generated_date': datetime.now().strftime('%B %d, %Y'),
                'brand_colors': self.brand_colors
            }
            
            # Generate content
            html_content = self._render_monthly_email_template(email_data)
            text_content = self._generate_text_version(email_data)
            
            return self._send_email_with_attachment(
                recipient_email=recipient_email,
                subject=subject,
                html_content=html_content,
                text_content=text_content,
                attachment_path=pdf_path,
                attachment_name=f"{artist_name}_Monthly_{period}.pdf"
            )
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def send_batch_reports(self, recipients: List[Dict]) -> Dict:
        """Send reports to multiple recipients"""
        results = {
            'sent': [],
            'failed': [],
            'total': len(recipients)
        }
        
        for recipient in recipients:
            try:
                if recipient.get('report_type') == 'wrapped':
                    result = self.send_wrapped_report(
                        recipient_email=recipient['email'],
                        pdf_path=recipient['pdf_path'],
                        artist_name=recipient['artist_name'],
                        year=recipient['year'],
                        additional_message=recipient.get('message')
                    )
                elif recipient.get('report_type') == 'monthly':
                    result = self.send_monthly_report(
                        recipient_email=recipient['email'],
                        pdf_path=recipient['pdf_path'],
                        artist_name=recipient['artist_name'],
                        period=recipient['period']
                    )
                
                if result.get('success'):
                    results['sent'].append(recipient['email'])
                else:
                    results['failed'].append({
                        'email': recipient['email'],
                        'error': result.get('error')
                    })
                    
            except Exception as e:
                results['failed'].append({
                    'email': recipient.get('email', 'unknown'),
                    'error': str(e)
                })
        
        return results
    
    def send_notification_email(self, recipient_email: str, subject: str, 
                               content: str, is_html: bool = False) -> Dict:
        """Send general notification email"""
        try:
            if is_html:
                html_content = content
                text_content = self._html_to_text(content)
            else:
                text_content = content
                html_content = self._text_to_html(content)
            
            return self._send_email(
                recipient_email=recipient_email,
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _send_email_with_attachment(self, recipient_email: str, subject: str,
                                   html_content: str, text_content: str,
                                   attachment_path: str, attachment_name: str) -> Dict:
        """Send email with PDF attachment"""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = formataddr((self.from_name, self.from_email))
            msg['To'] = recipient_email
            msg['Subject'] = subject
            
            # Add text and HTML parts
            text_part = MIMEText(text_content, 'plain', 'utf-8')
            html_part = MIMEText(html_content, 'html', 'utf-8')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Add PDF attachment
            if os.path.exists(attachment_path):
                with open(attachment_path, 'rb') as f:
                    attachment = MIMEApplication(f.read(), _subtype='pdf')
                    attachment.add_header(
                        'Content-Disposition', 
                        f'attachment; filename="{attachment_name}"'
                    )
                    msg.attach(attachment)
            
            # Send email
            return self._send_smtp_email(msg, recipient_email)
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _send_email(self, recipient_email: str, subject: str,
                   html_content: str, text_content: str) -> Dict:
        """Send email without attachment"""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = formataddr((self.from_name, self.from_email))
            msg['To'] = recipient_email
            msg['Subject'] = subject
            
            # Add text and HTML parts
            text_part = MIMEText(text_content, 'plain', 'utf-8')
            html_part = MIMEText(html_content, 'html', 'utf-8')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Send email
            return self._send_smtp_email(msg, recipient_email)
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _send_smtp_email(self, msg: MIMEMultipart, recipient_email: str) -> Dict:
        """Send email via SMTP"""
        try:
            # Connect to SMTP server
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()  # Enable encryption
            
            # Login if credentials provided
            if self.smtp_username and self.smtp_password:
                server.login(self.smtp_username, self.smtp_password)
            
            # Send email
            text = msg.as_string()
            server.sendmail(self.from_email, recipient_email, text)
            server.quit()
            
            return {
                'success': True,
                'message': f'Email sent successfully to {recipient_email}',
                'sent_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _render_wrapped_email_template(self, data: Dict) -> str:
        """Render Wrapped email template"""
        template_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Your {data['year']} Music Wrapped</title>
    <style>
        body {{
            font-family: 'Arial', sans-serif;
            line-height: 1.6;
            color: {self.brand_colors['text']};
            background-color: #f8f9fa;
            margin: 0;
            padding: 0;
        }}
        .container {{
            max-width: 600px;
            margin: 0 auto;
            background-color: {self.brand_colors['background']};
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
        }}
        .header {{
            background: linear-gradient(135deg, {self.brand_colors['primary']} 0%, {self.brand_colors['accent']} 100%);
            color: white;
            padding: 40px 30px;
            text-align: center;
        }}
        .logo {{
            font-size: 24px;
            font-weight: bold;
            letter-spacing: 2px;
            margin-bottom: 20px;
        }}
        .title {{
            font-size: 32px;
            font-weight: bold;
            margin-bottom: 10px;
        }}
        .subtitle {{
            font-size: 18px;
            opacity: 0.9;
        }}
        .content {{
            padding: 40px 30px;
        }}
        .highlight {{
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid {self.brand_colors['accent']};
            margin: 20px 0;
        }}
        .button {{
            display: inline-block;
            background-color: {self.brand_colors['accent']};
            color: white;
            padding: 12px 30px;
            text-decoration: none;
            border-radius: 6px;
            font-weight: bold;
            margin: 20px 0;
        }}
        .footer {{
            background-color: #f8f9fa;
            padding: 30px;
            text-align: center;
            font-size: 14px;
            color: #666;
        }}
        .social-links {{
            margin-top: 20px;
        }}
        .social-links a {{
            color: {self.brand_colors['accent']};
            text-decoration: none;
            margin: 0 10px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">PRISM ANALYTICS</div>
            <div class="title">Your {data['year']} Music Wrapped</div>
            <div class="subtitle">Ready for {data['artist_name']}</div>
        </div>
        
        <div class="content">
            <h2>🎵 Hello {data['artist_name']}!</h2>
            
            <p>Your {data['year']} Music Wrapped report is ready! This comprehensive analysis shows your incredible journey through the year, including:</p>
            
            <div class="highlight">
                <h3>📊 What's Inside Your Report</h3>
                <ul>
                    <li><strong>Total Streams:</strong> Your complete streaming numbers</li>
                    <li><strong>Top Tracks:</strong> Your biggest hits of the year</li>
                    <li><strong>Global Reach:</strong> Countries where your music was heard</li>
                    <li><strong>Platform Performance:</strong> How you performed across different platforms</li>
                    <li><strong>Growth Insights:</strong> Your peak months and trending patterns</li>
                </ul>
            </div>
            
            <p>Your detailed PDF report is attached to this email. Open it to discover all the amazing milestones you achieved in {data['year']}!</p>
            
            {f'<div class="highlight"><h3>📝 Personal Message</h3><p>{data["additional_message"]}</p></div>' if data.get('additional_message') else ''}
            
            <p>Thank you for being part of the Prism Analytics family. Here's to another year of incredible music and even bigger achievements!</p>
            
            <p>Best regards,<br>
            <strong>The Prism Analytics Team</strong></p>
        </div>
        
        <div class="footer">
            <p>© {datetime.now().year} Prism Analytics • Music Data Intelligence Platform</p>
            <p>Generated on {data['generated_date']}</p>
            
            <div class="social-links">
                <a href="#">Website</a> •
                <a href="#">Support</a> •
                <a href="#">Privacy Policy</a>
            </div>
        </div>
    </div>
</body>
</html>
        """
        
        return template_html
    
    def _render_monthly_email_template(self, data: Dict) -> str:
        """Render monthly report email template"""
        template_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Monthly Performance Report</title>
    <style>
        body {{
            font-family: 'Arial', sans-serif;
            line-height: 1.6;
            color: {self.brand_colors['text']};
            background-color: #f8f9fa;
            margin: 0;
            padding: 0;
        }}
        .container {{
            max-width: 600px;
            margin: 0 auto;
            background-color: {self.brand_colors['background']};
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
        }}
        .header {{
            background: linear-gradient(135deg, {self.brand_colors['secondary']} 0%, {self.brand_colors['accent']} 100%);
            color: white;
            padding: 40px 30px;
            text-align: center;
        }}
        .logo {{
            font-size: 24px;
            font-weight: bold;
            letter-spacing: 2px;
            margin-bottom: 20px;
        }}
        .title {{
            font-size: 28px;
            font-weight: bold;
            margin-bottom: 10px;
        }}
        .subtitle {{
            font-size: 16px;
            opacity: 0.9;
        }}
        .content {{
            padding: 40px 30px;
        }}
        .highlight {{
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid {self.brand_colors['accent']};
            margin: 20px 0;
        }}
        .footer {{
            background-color: #f8f9fa;
            padding: 30px;
            text-align: center;
            font-size: 14px;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">PRISM ANALYTICS</div>
            <div class="title">Monthly Performance Report</div>
            <div class="subtitle">{data['artist_name']} • {data['period']}</div>
        </div>
        
        <div class="content">
            <h2>📊 Hello {data['artist_name']}!</h2>
            
            <p>Your monthly performance report for <strong>{data['period']}</strong> is ready! This report provides detailed insights into your music performance this month.</p>
            
            <div class="highlight">
                <h3>📈 Monthly Highlights</h3>
                <ul>
                    <li><strong>Streaming Performance:</strong> Total plays across all platforms</li>
                    <li><strong>Top Performing Tracks:</strong> Your biggest hits this month</li>
                    <li><strong>Geographic Insights:</strong> Where your music is being discovered</li>
                    <li><strong>Platform Breakdown:</strong> Performance across different services</li>
                    <li><strong>Growth Trends:</strong> Month-over-month comparisons</li>
                </ul>
            </div>
            
            <p>Your detailed PDF report is attached. Review your performance and discover opportunities for the month ahead!</p>
            
            <p>Best regards,<br>
            <strong>The Prism Analytics Team</strong></p>
        </div>
        
        <div class="footer">
            <p>© {datetime.now().year} Prism Analytics • Monthly Performance Reports</p>
            <p>Generated on {data['generated_date']}</p>
        </div>
    </div>
</body>
</html>
        """
        
        return template_html
    
    def _generate_text_version(self, data: Dict) -> str:
        """Generate plain text version of email"""
        text = f"""
PRISM ANALYTICS - {data['report_type'].upper()} REPORT

Hello {data['artist_name']}!

Your {data.get('year', data.get('period', ''))} {data['report_type']} report is ready!

This comprehensive analysis includes:
- Total streaming performance
- Top performing tracks  
- Global reach and geographic insights
- Platform performance breakdown
- Growth trends and insights

Your detailed PDF report is attached to this email.

{"Personal Message: " + data['additional_message'] if data.get('additional_message') else ''}

Thank you for being part of the Prism Analytics family!

Best regards,
The Prism Analytics Team

Generated on {data['generated_date']}
© {datetime.now().year} Prism Analytics • Music Data Intelligence Platform
        """
        
        return text.strip()
    
    def _html_to_text(self, html: str) -> str:
        """Convert HTML to plain text (simple version)"""
        import re
        # Remove HTML tags
        text = re.sub('<[^<]+?>', '', html)
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def _text_to_html(self, text: str) -> str:
        """Convert plain text to HTML"""
        # Convert line breaks to <br>
        html = text.replace('\n', '<br>')
        # Wrap in basic HTML structure
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                {html}
            </div>
        </body>
        </html>
        """
        return html
    
    def test_email_configuration(self) -> Dict:
        """Test email configuration"""
        try:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            
            if self.smtp_username and self.smtp_password:
                server.login(self.smtp_username, self.smtp_password)
            
            server.quit()
            
            return {
                'success': True,
                'message': 'Email configuration is valid',
                'smtp_server': self.smtp_server,
                'smtp_port': self.smtp_port
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'smtp_server': self.smtp_server,
                'smtp_port': self.smtp_port
            }

# Example usage
if __name__ == "__main__":
    email_service = EmailService()
    
    # Test configuration
    config_test = email_service.test_email_configuration()
    print("Email configuration test:", config_test)
    
    # Example: Send wrapped report
    if config_test['success']:
        result = email_service.send_wrapped_report(
            recipient_email="artist@example.com",
            pdf_path="/path/to/wrapped_report.pdf",
            artist_name="Taylor Swift",
            year=2024,
            additional_message="Amazing year! Looking forward to 2025!"
        )
        print("Email send result:", result)