import io
import qrcode
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, black, white
from reportlab.pdfgen import canvas
from django.conf import settings
from django.utils import timezone
from io import BytesIO
import os


class CertificateService:
    """Service for generating membership certificates and ID cards"""
    
    def __init__(self):
        self.primary_green = HexColor('#2E7D32')
        self.light_green = HexColor('#4CAF50')
        self.accent_green = HexColor('#66BB6A')
        
    def generate_qr_code(self, data, size=150):
        """Generate QR code for verification"""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to bytes
        img_buffer = BytesIO()
        img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        return img_buffer
    
    def _draw_photo_placeholder(self, p, photo_x, photo_y, photo_size):
        """Draw a placeholder when no photo is available"""
        # Inner photo square
        p.setStrokeColor(self.light_green)
        p.setFillColor(HexColor('#FAFAFA'))
        p.setLineWidth(1)
        p.rect(photo_x + 0.05 * inch, photo_y + 0.05 * inch, 
               photo_size - 0.1 * inch, photo_size - 0.1 * inch, stroke=1, fill=1)
        
        # Photo placeholder text
        p.setFillColor(HexColor('#888888'))
        p.setFont("Helvetica", 10)
        p.drawCentredString(photo_x + photo_size/2, photo_y + photo_size/2, "PHOTO")
    
    def generate_membership_certificate(self, membership):
        """Generate PDF membership certificate in landscape orientation"""
        buffer = io.BytesIO()
        
        # Create the PDF object in landscape orientation
        from reportlab.lib.pagesizes import landscape
        p = canvas.Canvas(buffer, pagesize=landscape(A4))
        width, height = landscape(A4)  # width=842, height=595
        
        # Landscape certificate design
        
        # Header section with elegant design
        header_height = 80
        p.setFillColor(self.primary_green)
        p.rect(0, height - header_height, width, header_height, fill=1, stroke=0)
        
        # Decorative top strip
        p.setFillColor(self.light_green)
        p.rect(0, height - 15, width, 15, fill=1, stroke=0)
        
        # Header text
        p.setFillColor(white)
        p.setFont("Helvetica-Bold", 28)
        p.drawCentredString(width / 2, height - 45, "AKILIMO NIGERIA ASSOCIATION")
        
        p.setFont("Helvetica-Bold", 16)
        p.drawCentredString(width / 2, height - 70, "MEMBERSHIP CERTIFICATE")
        
        # Logo section (left side) - with transparent background handling
        logo_path = "/Users/Apple/projects/ana_pro/ana_logo.png"
        logo_x = 50
        logo_y = height - 150
        logo_size = 80
        
        try:
            if os.path.exists(logo_path):
                # Add white background behind logo to handle transparency
                p.setFillColor(white)
                p.setStrokeColor(white)
                p.rect(logo_x - 5, logo_y - 5, logo_size + 10, logo_size + 10, fill=1, stroke=0)
                
                # Draw the logo
                p.drawImage(logo_path, logo_x, logo_y, logo_size, logo_size, mask='auto')
            else:
                # Fallback logo design
                p.setStrokeColor(self.primary_green)
                p.setFillColor(self.light_green)
                p.circle(logo_x + logo_size/2, logo_y + logo_size/2, logo_size/2, stroke=2, fill=1)
                p.setFillColor(white)
                p.setFont("Helvetica-Bold", 12)
                p.drawCentredString(logo_x + logo_size/2, logo_y + logo_size/2, "ANA")
        except:
            # Fallback design
            p.setStrokeColor(self.primary_green)
            p.setFillColor(self.light_green)
            p.circle(logo_x + logo_size/2, logo_y + logo_size/2, logo_size/2, stroke=2, fill=1)
            p.setFillColor(white)
            p.setFont("Helvetica-Bold", 12)
            p.drawCentredString(logo_x + logo_size/2, logo_y + logo_size/2, "ANA")
        
        # Main content area with landscape layout
        p.setFillColor(black)
        
        # "This is to certify that" text
        p.setFont("Helvetica", 16)
        p.drawCentredString(width / 2, height - 120, "This is to certify that")
        
        # Member name section - clean without background boxes
        name_section_y = height - 180
        
        # Member name - prominent and centered
        p.setFillColor(self.primary_green)
        p.setFont("Helvetica-Bold", 36)
        member_name = membership.member.get_full_name() or membership.member.username
        p.drawCentredString(width / 2, name_section_y, member_name.upper())
        
        # Certificate description
        p.setFillColor(black)
        p.setFont("Helvetica", 18)
        p.drawCentredString(width / 2, height - 240, "is a registered member of the AKILIMO Nigeria Association")
        
        # Membership type emphasis
        p.setFont("Helvetica-Bold", 14)
        p.drawCentredString(width / 2, height - 265, f"({membership.get_membership_type_display()})")
        
        # Three-column details section - clean layout without background boxes
        details_y = height - 310
        col_width = (width - 160) / 3
        
        # Left column - Certificate details (no background box)
        p.setFillColor(black)
        p.setFont("Helvetica-Bold", 12)
        p.drawString(80, details_y - 20, "CERTIFICATE DETAILS")
        p.setFont("Helvetica", 10)
        p.drawString(80, details_y - 35, f"Certificate No: {membership.certificate_number}")
        p.drawString(80, details_y - 48, f"Issue Date: {timezone.now().strftime('%B %d, %Y')}")
        p.drawString(80, details_y - 61, f"Member ID: {str(membership.membership_id)[:8]}...")
        
        # Middle column - Membership details (no background box)
        mid_x = 60 + col_width + 20
        p.setFont("Helvetica-Bold", 12)
        p.drawString(mid_x + 20, details_y - 20, "MEMBERSHIP INFO")
        p.setFont("Helvetica", 10)
        p.drawString(mid_x + 20, details_y - 35, f"Type: {membership.get_membership_type_display()}")
        p.drawString(mid_x + 20, details_y - 48, f"Valid From: {membership.start_date.strftime('%b %d, %Y')}")
        p.drawString(mid_x + 20, details_y - 61, f"Valid Until: {membership.end_date.strftime('%b %d, %Y')}")
        
        # Right column - Status and verification (no background box)
        right_x = mid_x + col_width + 20
        p.setFont("Helvetica-Bold", 12)
        p.drawString(right_x + 20, details_y - 20, "STATUS & VERIFICATION")
        p.setFont("Helvetica", 10)
        p.drawString(right_x + 20, details_y - 35, "Status: ACTIVE")
        p.drawString(right_x + 20, details_y - 48, "Scan QR code to verify")
        
        # Partner organization if available
        if hasattr(membership.member, 'profile') and membership.member.profile.partner_name:
            p.setFont("Helvetica-Oblique", 12)
            p.setFillColor(HexColor('#555555'))
            p.drawCentredString(width / 2, details_y - 90, f"Partner Organization: {membership.member.profile.partner_name}")
        
        # QR Code for verification (positioned on the right side)
        verification_url = f"{settings.SITE_URL if hasattr(settings, 'SITE_URL') else 'https://ana.example.com'}/verify/{membership.qr_code}"
        qr_buffer = self.generate_qr_code(verification_url)
        
        # Save QR code as temporary image
        temp_qr_path = f"/tmp/qr_{membership.membership_id}.png"
        with open(temp_qr_path, 'wb') as f:
            f.write(qr_buffer.getvalue())
        
        # Add QR code to the far right
        try:
            qr_size = 80
            qr_x = width - qr_size - 50
            qr_y = height - 200
            
            # QR code background frame
            p.setStrokeColor(self.primary_green)
            p.setFillColor(white)
            p.setLineWidth(2)
            p.rect(qr_x - 5, qr_y - 5, qr_size + 10, qr_size + 10, fill=1, stroke=1)
            
            p.drawImage(temp_qr_path, qr_x, qr_y, qr_size, qr_size)
            
            # QR label
            p.setFillColor(black)
            p.setFont("Helvetica", 8)
            p.drawCentredString(qr_x + qr_size/2, qr_y - 15, "Scan to Verify")
            
            # Clean up temporary file
            os.remove(temp_qr_path)
        except:
            pass  # If QR code fails, continue without it
        
        # Footer section with landscape design
        footer_y = 80
        
        # Clean footer without background box
        
        # Three signature sections
        sig_width = (width - 200) / 3
        
        # Left signature - Secretary General
        p.setFillColor(black)
        p.line(100, 50, 100 + sig_width - 40, 50)
        p.setFont("Helvetica", 10)
        p.drawCentredString(100 + (sig_width - 40)/2, 35, "Secretary General")
        
        # Center - Certificate validity text
        p.setFont("Helvetica-Bold", 10)
        p.drawCentredString(width / 2, 60, "CERTIFICATE OF MEMBERSHIP")
        p.setFont("Helvetica", 8)
        p.drawCentredString(width / 2, 45, "This certificate is valid only with proper verification")
        p.drawCentredString(width / 2, 35, f"and remains active until {membership.end_date.strftime('%B %d, %Y')}")
        
        # Right signature - President
        right_sig_x = width - 100 - sig_width + 40
        p.line(right_sig_x, 50, width - 100, 50)
        p.drawCentredString(right_sig_x + (sig_width - 40)/2, 35, "President")
        
        # Decorative elements
        p.setStrokeColor(self.light_green)
        p.setLineWidth(1)
        # Left decorative line
        p.line(60, footer_y/2 + 10, 150, footer_y/2 + 10)
        # Right decorative line
        p.line(width - 150, footer_y/2 + 10, width - 60, footer_y/2 + 10)
        
        # Add decorative border around entire certificate
        p.setStrokeColor(self.primary_green)
        p.setLineWidth(3)
        p.rect(10, 10, width - 20, height - 20, fill=0, stroke=1)
        
        # Inner decorative border
        p.setStrokeColor(self.light_green)
        p.setLineWidth(1)
        p.rect(20, 20, width - 40, height - 40, fill=0, stroke=1)
        
        # Finalize
        p.showPage()
        p.save()
        
        buffer.seek(0)
        return buffer
    
    def generate_id_card(self, membership):
        """Generate modern portrait PDF ID card with logo"""
        buffer = io.BytesIO()
        
        # Create portrait ID card (2.5" x 4") - modern portrait design
        card_width = 2.5 * inch
        card_height = 4 * inch
        
        p = canvas.Canvas(buffer, pagesize=(card_width, card_height))
        
        # Modern gradient-style header
        p.setFillColor(self.primary_green)
        p.rect(0, card_height - 0.8 * inch, card_width, 0.8 * inch, fill=1, stroke=0)
        
        # Subtle accent strip
        p.setFillColor(self.light_green)
        p.rect(0, card_height - 0.85 * inch, card_width, 0.05 * inch, fill=1, stroke=0)
        
        # Logo section (top center)
        logo_path = "/Users/Apple/projects/ana_pro/ana_logo.png"
        logo_size = 0.4 * inch
        logo_x = (card_width - logo_size) / 2
        logo_y = card_height - 0.55 * inch
        
        try:
            if os.path.exists(logo_path):
                # White background for logo clarity
                p.setFillColor(white)
                p.circle(logo_x + logo_size/2, logo_y + logo_size/2, logo_size/2 + 0.02 * inch, fill=1, stroke=0)
                # Draw the logo
                p.drawImage(logo_path, logo_x, logo_y, logo_size, logo_size, mask='auto')
            else:
                # Fallback logo design
                p.setStrokeColor(white)
                p.setFillColor(self.light_green)
                p.setLineWidth(2)
                p.circle(logo_x + logo_size/2, logo_y + logo_size/2, logo_size/2, stroke=1, fill=1)
                p.setFillColor(white)
                p.setFont("Helvetica-Bold", 8)
                p.drawCentredString(logo_x + logo_size/2, logo_y + logo_size/2, "ANA")
        except:
            # Fallback design
            p.setStrokeColor(white)
            p.setFillColor(self.light_green)
            p.setLineWidth(2)
            p.circle(logo_x + logo_size/2, logo_y + logo_size/2, logo_size/2, stroke=1, fill=1)
            p.setFillColor(white)
            p.setFont("Helvetica-Bold", 8)
            p.drawCentredString(logo_x + logo_size/2, logo_y + logo_size/2, "ANA")
        
        # Organization name (compact but readable)
        p.setFillColor(white)
        p.setFont("Helvetica-Bold", 9)
        p.drawCentredString(card_width / 2, card_height - 0.7 * inch, "AKILIMO NIGERIA")
        p.setFont("Helvetica-Bold", 7)
        p.drawCentredString(card_width / 2, card_height - 0.78 * inch, "ASSOCIATION")
        
        # Member photo section (modern square design)
        photo_size = 1.2 * inch
        photo_x = (card_width - photo_size) / 2
        photo_y = card_height - 2.2 * inch
        
        # Modern square photo frame
        p.setStrokeColor(self.primary_green)
        p.setFillColor(HexColor('#F8F8F8'))
        p.setLineWidth(3)
        p.rect(photo_x, photo_y, photo_size, photo_size, stroke=1, fill=1)
        
        # Try to load and display profile photo
        try:
            if hasattr(membership.member, 'profile') and membership.member.profile.profile_photo:
                photo_path = membership.member.profile.profile_photo.path
                if os.path.exists(photo_path):
                    # Create a circular mask for the photo
                    p.drawImage(photo_path, photo_x + 0.05 * inch, photo_y + 0.05 * inch, 
                               photo_size - 0.1 * inch, photo_size - 0.1 * inch, mask='auto')
                else:
                    # Fallback to placeholder
                    self._draw_photo_placeholder(p, photo_x, photo_y, photo_size)
            else:
                # No photo uploaded - show placeholder
                self._draw_photo_placeholder(p, photo_x, photo_y, photo_size)
        except:
            # Error loading photo - show placeholder
            self._draw_photo_placeholder(p, photo_x, photo_y, photo_size)
        
        # Member name section (prominent and centered)
        name_y = card_height - 2.5 * inch
        p.setFillColor(self.primary_green)
        p.setFont("Helvetica-Bold", 12)
        member_name = membership.member.get_full_name() or membership.member.username
        
        # Truncate long names for card space
        if len(member_name) > 18:
            member_name = member_name[:18] + "..."
        
        p.drawCentredString(card_width / 2, name_y, member_name.upper())
        
        # Membership type badge
        p.setFillColor(self.light_green)
        p.setFont("Helvetica-Bold", 8)
        membership_type = membership.get_membership_type_display()
        p.drawCentredString(card_width / 2, name_y - 0.2 * inch, membership_type.upper())
        
        # Clean details section
        details_y = card_height - 3 * inch
        p.setFillColor(black)
        
        # ID Number
        p.setFont("Helvetica-Bold", 8)
        p.drawCentredString(card_width / 2, details_y, "MEMBER ID")
        p.setFont("Helvetica", 9)
        p.drawCentredString(card_width / 2, details_y - 0.15 * inch, membership.certificate_number)
        
        # Valid until
        p.setFont("Helvetica-Bold", 8)
        p.drawCentredString(card_width / 2, details_y - 0.35 * inch, "VALID UNTIL")
        p.setFont("Helvetica", 9)
        p.drawCentredString(card_width / 2, details_y - 0.5 * inch, membership.end_date.strftime('%m/%Y'))
        
        # Status
        p.setFont("Helvetica-Bold", 8)
        p.setFillColor(self.primary_green)
        p.drawCentredString(card_width / 2, details_y - 0.7 * inch, "ACTIVE")
        
        # Partner organization (if available) - moved up for better spacing
        if hasattr(membership.member, 'profile') and membership.member.profile.partner_name:
            partner_name = membership.member.profile.partner_name
            if len(partner_name) > 20:
                partner_name = partner_name[:20] + "..."
            p.setFont("Helvetica-Oblique", 7)
            p.setFillColor(HexColor('#666666'))
            p.drawCentredString(card_width / 2, details_y - 0.85 * inch, partner_name)
        
        # Issue date (bottom of front) - moved down to avoid overlap
        p.setFillColor(HexColor('#888888'))
        p.setFont("Helvetica", 6)
        p.drawCentredString(card_width / 2, 0.05 * inch, f"Issued: {timezone.now().strftime('%m/%d/%Y')}")
        
        # Modern card border for front
        p.setStrokeColor(self.primary_green)
        p.setLineWidth(2)
        p.rect(0, 0, card_width, card_height, fill=0, stroke=1)
        
        # Start new page for back of card
        p.showPage()
        
        # === BACK OF CARD === 
        
        # Back background with subtle design
        p.setFillColor(HexColor('#FAFAFA'))
        p.rect(0, 0, card_width, card_height, fill=1, stroke=0)
        
        # Header section for back
        p.setFillColor(self.primary_green)
        p.rect(0, card_height - 0.6 * inch, card_width, 0.6 * inch, fill=1, stroke=0)
        
        # Back header text
        p.setFillColor(white)
        p.setFont("Helvetica-Bold", 10)
        p.drawCentredString(card_width / 2, card_height - 0.25 * inch, "VERIFICATION")
        p.setFont("Helvetica-Bold", 8)
        p.drawCentredString(card_width / 2, card_height - 0.4 * inch, "& MEMBERSHIP DETAILS")
        
        # Large QR Code (prominent on back) - positioned higher for better spacing
        verification_url = f"{settings.SITE_URL if hasattr(settings, 'SITE_URL') else 'https://akilimonigeria.org'}/verify/{membership.qr_code}"
        qr_buffer = self.generate_qr_code(verification_url, size=120)
        
        temp_qr_path = f"/tmp/qr_card_{membership.membership_id}.png"
        with open(temp_qr_path, 'wb') as f:
            f.write(qr_buffer.getvalue())
        
        try:
            # Large QR code - centered and positioned for better spacing
            qr_size = 1.5 * inch
            qr_x = (card_width - qr_size) / 2
            qr_y = card_height - 2.3 * inch
            
            # QR background with modern design
            p.setStrokeColor(self.primary_green)
            p.setFillColor(white)
            p.setLineWidth(3)
            p.rect(qr_x - 0.1 * inch, qr_y - 0.1 * inch, 
                   qr_size + 0.2 * inch, qr_size + 0.2 * inch, fill=1, stroke=1)
            
            # Inner border
            p.setStrokeColor(self.light_green)
            p.setLineWidth(1)
            p.rect(qr_x - 0.05 * inch, qr_y - 0.05 * inch, 
                   qr_size + 0.1 * inch, qr_size + 0.1 * inch, fill=0, stroke=1)
            
            p.drawImage(temp_qr_path, qr_x, qr_y, qr_size, qr_size)
            
            # QR instructions - better spacing
            p.setFillColor(self.primary_green)
            p.setFont("Helvetica-Bold", 10)
            p.drawCentredString(card_width / 2, qr_y - 0.3 * inch, "SCAN TO VERIFY")
            
            p.setFillColor(black)
            p.setFont("Helvetica", 8)
            p.drawCentredString(card_width / 2, qr_y - 0.45 * inch, "Use any QR code scanner")
            p.drawCentredString(card_width / 2, qr_y - 0.58 * inch, "to verify membership status")
            
            os.remove(temp_qr_path)
        except:
            # Fallback if QR fails
            p.setFillColor(self.primary_green)
            p.setFont("Helvetica-Bold", 12)
            p.drawCentredString(card_width / 2, card_height / 2, "VERIFICATION")
            p.setFont("Helvetica", 10)
            p.drawCentredString(card_width / 2, card_height / 2 - 0.2 * inch, "QR Code Available")
        
        # Status information - positioned in middle section for better spacing
        status_y = card_height - 3 * inch
        p.setFillColor(self.primary_green)
        p.setFont("Helvetica-Bold", 10)
        p.drawCentredString(card_width / 2, status_y, "ACTIVE MEMBER")
        
        # Contact information - moved much lower for clear separation
        contact_y = 0.75 * inch
        p.setFillColor(HexColor('#666666'))
        p.setFont("Helvetica-Bold", 8)
        p.drawCentredString(card_width / 2, contact_y, "AKILIMO NIGERIA ASSOCIATION")
        
        p.setFont("Helvetica", 7)
        p.drawCentredString(card_width / 2, contact_y - 0.15 * inch, "For inquiries:")
        p.drawCentredString(card_width / 2, contact_y - 0.3 * inch, "info@akilimonigeria.org")
        
        p.drawCentredString(card_width / 2, contact_y - 0.4 * inch, "Visit us online:")
        p.drawCentredString(card_width / 2, contact_y - 0.5 * inch, "www.akilimonigeria.org")
        
        # Back border
        p.setStrokeColor(self.primary_green)
        p.setLineWidth(2)
        p.rect(0, 0, card_width, card_height, fill=0, stroke=1)
        
        # Finalize both pages
        p.showPage()
        p.save()
        
        buffer.seek(0)
        return buffer