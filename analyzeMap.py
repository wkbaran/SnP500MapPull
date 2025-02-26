import os
import json
import time
import base64
import requests
from datetime import datetime
import pytz
from dotenv import load_dotenv
import smtplib
import re
import markdown
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.application import MIMEApplication
from jinja2 import Environment, FileSystemLoader

class SP500HeatMapAnalyzer:
    def __init__(self, api_key, api_endpoint, image_path, storage_dir="./data", max_previous=4,
                 email_enabled=False, email_sender="", email_recipients=None,
                 smtp_server="", smtp_port=587, smtp_username="", smtp_password="",
                 templates_dir="./templates"):
        self.api_key = api_key
        self.api_endpoint = api_endpoint
        self.image_path = image_path
        self.storage_dir = storage_dir
        self.max_previous = max_previous

        # Email settings
        self.email_enabled = email_enabled
        self.email_sender = email_sender
        self.email_recipients = email_recipients if email_recipients else []

        # SMTP settings
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.smtp_username = smtp_username
        self.smtp_password = smtp_password

        # Create storage directory if it doesn't exist
        if not os.path.exists(storage_dir):
            os.makedirs(storage_dir)

    """Encode the image as base64 for API submission."""
    def encode_image(self):
        with open(self.image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    """Get the most recent analysis if it exists."""
    def get_previous_analysis(self):
        analysis_files = [f for f in os.listdir(self.storage_dir) if f.endswith('.json')]
        if not analysis_files:
            return None

        # Sort by timestamp in filename (assuming format: analysis_TIMESTAMP.json)
        sorted_files = sorted(analysis_files, reverse=True)

        # Limit to max_previous most recent analyses
        recent_files = sorted_files[:self.max_previous]

        # Get the most recent analysis
        latest_file = recent_files[0]
        with open(os.path.join(self.storage_dir, latest_file), 'r') as f:
            return json.load(f)

    """Save the current analysis to the storage directory."""
    def save_analysis(self, analysis):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"analysis_{timestamp}.json"
        filepath = os.path.join(self.storage_dir, filename)

        with open(filepath, 'w') as f:
            json.dump(analysis, f, indent=2)

        return filepath

    """Extract the formatted text from previous analysis response."""
    def extract_previous_analysis_text(self, previous_analysis):
        if not previous_analysis:
            return None

        # Extract the actual analysis text from the response
        if "choices" in previous_analysis["response"]:
            # For OpenAI API format
            return previous_analysis["response"]["choices"][0]["message"]["content"]
        else:
            # Fallback if the response structure is different
            return str(previous_analysis["response"])

    """Generate the prompt for the API based on previous analysis."""
    def generate_prompt(self, previous_analysis):
        # Get current date, day of the week, and time in both local and EST
        now_local = datetime.now()
        local_tz = datetime.now().astimezone().tzinfo

        # Convert to EST
        est_tz = pytz.timezone('US/Eastern')
        now_est = datetime.now(est_tz)

        # Format date and times
        current_date = now_local.strftime("%Y-%m-%d")
        day_of_week = now_local.strftime("%A")
        local_time = now_local.strftime("%H:%M:%S %Z")
        est_time = now_est.strftime("%H:%M:%S %Z")

        date_info = f"""Current date: {current_date} ({day_of_week})
Local time: {local_time}
Market time (EST): {est_time}"""

        if previous_analysis:
            # Extract readable text from previous analysis
            previous_text = self.extract_previous_analysis_text(previous_analysis)
            previous_timestamp = previous_analysis.get("timestamp", "Unknown time")

            return f"""
            {date_info}
            
            Analyze this S&P 500 Heat Map image. 
            
            1. Identify the overall market trend (bullish/bearish)
            2. Note which sectors are performing the best and worst
            3. Identify any notable outlier stocks (significant gains or losses)
            4. Compare with the previous analysis and highlight key changes:
               - Change in overall market sentiment
               - Sectors that have improved or deteriorated
               - New outlier stocks that have emerged
            
            Previous analysis from {previous_timestamp}:
            
            {previous_text}
            """
        else:
            return f"""
            {date_info}
            
            Analyze this S&P 500 Heat Map image. 
            
            1. Identify the overall market trend (bullish/bearish)
            2. Note which sectors are performing the best and worst
            3. Identify any notable outlier stocks (significant gains or losses)
            """

    """Submit the heat map image to the AI API for analysis."""
    def analyze_heatmap(self):
        base64_image = self.encode_image()
        previous_analysis = self.get_previous_analysis()
        prompt = self.generate_prompt(previous_analysis)

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        payload = {
            "model": "gpt-4o", # Use appropriate model that can process images
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 1000
        }

        # Send the request to the API
        response = requests.post(self.api_endpoint, headers=headers, json=payload)

        if response.status_code == 200:
            analysis_result = response.json()

            # Get current date, day of week, and times for metadata
            now_local = datetime.now()
            local_tz = datetime.now().astimezone().tzinfo

            # Convert to EST
            est_tz = pytz.timezone('US/Eastern')
            now_est = datetime.now(est_tz)

            # Construct full analysis with metadata
            analysis = {
                "timestamp": now_local.isoformat(),
                "date": now_local.strftime("%Y-%m-%d"),
                "day_of_week": now_local.strftime("%A"),
                "local_time": now_local.strftime("%H:%M:%S"),
                "local_timezone": str(local_tz),
                "est_time": now_est.strftime("%H:%M:%S"),
                "est_timezone": "US/Eastern",
                "image_path": self.image_path,
                "prompt": prompt,
                "response": analysis_result,
                "previous_analysis_available": previous_analysis is not None
            }

            # Save the analysis
            saved_path = self.save_analysis(analysis)
            print(f"Analysis saved to {saved_path}")

            # Get analysis content
            analysis_content = None
            if "choices" in analysis_result:
                analysis_content = analysis_result["choices"][0]["message"]["content"]

            # Send email if enabled
            if self.email_enabled and analysis_content:
                self.send_email_notification(analysis_content, now_local, now_est)

            return analysis
        else:
            print(f"Error: API request failed with status code {response.status_code}")
            print(response.text)
            return None

    """Convert markdown to HTML with special handling for code blocks"""
    def markdown_to_html(self, text):
        if not text:
            return ""

        # Convert markdown to HTML
        html = markdown.markdown(text, extensions=['tables', 'fenced_code'])

        # Apply additional styling for better email rendering
        # Make code blocks look nicer
        html = html.replace('<code>', '<code style="background-color: #f5f5f5; padding: 2px 4px; border-radius: 4px; font-family: monospace;">')

        # Style pre blocks for code blocks
        html = html.replace('<pre>', '<pre style="background-color: #f5f5f5; padding: 10px; border-radius: 4px; overflow-x: auto; font-family: monospace; line-height: 1.4;">')

        # Style blockquotes
        html = html.replace('<blockquote>', '<blockquote style="border-left: 4px solid #ddd; padding-left: 15px; color: #666;">')

        # Style tables
        html = html.replace('<table>', '<table style="border-collapse: collapse; width: 100%; margin: 16px 0;">')
        html = html.replace('<th>', '<th style="border: 1px solid #ddd; padding: 8px; text-align: left; background-color: #f5f5f5;">')
        html = html.replace('<td>', '<td style="border: 1px solid #ddd; padding: 8px; text-align: left;">')

        return html

    """Send the analysis results via SMTP."""
    def send_email_notification(self, analysis_content, local_time, est_time):
        if not self.email_enabled or not self.email_recipients:
            return

        try:
            # Create email message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f'S&P 500 Heat Map Analysis - {local_time.strftime("%Y-%m-%d %H:%M")} / EST: {est_time.strftime("%H:%M")}'
            msg['From'] = self.email_sender
            msg['To'] = ", ".join(self.email_recipients)

            # Plain text version - strip markdown formatting for plain text
            plain_text = analysis_content
            # Remove markdown heading markers
            plain_text = re.sub(r'^#+\s+', '', plain_text, flags=re.MULTILINE)
            # Remove markdown bold/italic markers
            plain_text = re.sub(r'\*\*(.*?)\*\*', r'\1', plain_text)
            plain_text = re.sub(r'\*(.*?)\*', r'\1', plain_text)
            # Remove markdown links
            plain_text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', plain_text)

            text_content = f"""
S&P 500 Heat Map Analysis
Date: {local_time.strftime("%Y-%m-%d")} ({local_time.strftime("%A")})
Local Time: {local_time.strftime("%H:%M:%S %Z")}
Market Time (EST): {est_time.strftime("%H:%M:%S %Z")}

Analysis Results:
{plain_text}

This is an automated message from your S&P 500 Heat Map Analyzer.
            """

            # Convert markdown to HTML
            analysis_html = self.markdown_to_html(analysis_content)

            # HTML version with converted markdown
            html_content = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.5; color: #333; }}
                    .header {{ background-color: #f5f5f5; padding: 15px; margin-bottom: 20px; border-radius: 5px; }}
                    .content {{ padding: 0 20px; }}
                    .footer {{ font-size: 12px; color: #666; margin-top: 30px; border-top: 1px solid #eee; padding-top: 10px; }}
                    h1, h2, h3 {{ color: #444; }}
                    ul, ol {{ padding-left: 25px; }}
                    li {{ margin-bottom: 5px; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>S&P 500 Heat Map Analysis</h1>
                    <p>
                        <strong>Date:</strong> {local_time.strftime("%Y-%m-%d")} ({local_time.strftime("%A")})<br>
                        <strong>Local Time:</strong> {local_time.strftime("%H:%M:%S %Z")}<br>
                        <strong>Market Time (EST):</strong> {est_time.strftime("%H:%M:%S %Z")}
                    </p>
                </div>
                <div class="content">
                    <h2>Analysis Results:</h2>
                    {analysis_html}
                </div>
                <div class="footer">
                    <p>This is an automated message from your S&P 500 Heat Map Analyzer.</p>
                </div>
            </body>
            </html>
            """

            # Attach text and HTML parts
            part1 = MIMEText(text_content, 'plain')
            part2 = MIMEText(html_content, 'html')
            msg.attach(part1)
            msg.attach(part2)

            # Attach the image
            if os.path.exists(self.image_path):
                with open(self.image_path, 'rb') as img_file:
                    img_data = img_file.read()

                    # Create a unique content ID for the image
                    content_id = f"<heatmap_{datetime.now().strftime('%Y%m%d%H%M%S')}@analyzer>"

                    # Attach image with content ID
                    image = MIMEImage(img_data, name=os.path.basename(self.image_path))
                    image.add_header('Content-ID', content_id)
                    image.add_header('Content-Disposition', 'inline', filename=os.path.basename(self.image_path))
                    msg.attach(image)

                    # Also attach as regular attachment for email clients that don't display inline images
                    attachment = MIMEImage(img_data, name=os.path.basename(self.image_path))
                    attachment.add_header('Content-Disposition', 'attachment', filename=os.path.basename(self.image_path))
                    msg.attach(attachment)

            # Connect to SMTP server and send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()

                # Login if credentials provided
                if self.smtp_username and self.smtp_password:
                    server.login(self.smtp_username, self.smtp_password)

                # Send email
                server.send_message(msg)
                print(f"Email sent to {', '.join(self.email_recipients)}")

        except Exception as e:
            print(f"Error sending email: {str(e)}")


if __name__ == "__main__":
    load_dotenv()

    # Run the analysis
    analyzer = SP500HeatMapAnalyzer(
        os.getenv("API_KEY"),
        os.getenv("API_ENDPOINT"),
        os.getenv("IMAGE_PATH"),
        max_previous=int(os.getenv("MAX_PREVIOUS", "4")),
        email_enabled=os.getenv("EMAIL_ENABLED", "false").lower() == "true",
        email_sender=os.getenv("EMAIL_SENDER", ""),
        email_recipients=os.getenv("EMAIL_RECIPIENTS", "").split(",") if os.getenv("EMAIL_RECIPIENTS") else [],
        smtp_server=os.getenv("SMTP_SERVER", ""),
        smtp_port=int(os.getenv("SMTP_PORT", "587")),
        smtp_username=os.getenv("SMTP_USERNAME", ""),
        smtp_password=os.getenv("SMTP_PASSWORD", ""),
        templates_dir=os.getenv("TEMPLATES_DIR", "./templates")
    )

    analysis_result = analyzer.analyze_heatmap()

    if analysis_result:
        # Print the AI's analysis
        if "choices" in analysis_result["response"]:
            print("\nAI Analysis:")
            print(analysis_result["response"]["choices"][0]["message"]["content"])
        else:
            print("\nAI Analysis:", analysis_result["response"])