import yagmail
import datetime
from config import config
import logging

template = (
'<!DOCTYPE html>'
'<html lang="en" xmlns="https://www.w3.org/1999/xhtml" xmlns:o="urn:schemas-microsoft-com:office:office">'
'<head>'
' <meta charset="utf-8">'
' <meta name="viewport" content="width=device-width,initial-scale=1">'
' <meta name="x-apple-disable-message-reformatting">'
' <title></title>'
'</head>'
'<body style="margin:0;padding:0;word-spacing:normal;background-color:#939297;">'
' <div role="article" aria-roledescription="email" lang="en" style="text-size-adjust:100%;-webkit-text-size-adjust:100%;-ms-text-size-adjust:100%;background-color:#939297;">'
'  <br>'
'  <br>'
'  <table role="presentation" style="width:100%;border:none;border-spacing:0;">'
'   <tr>'
'    <td align="center" style="padding:0;">'
'     <table role="presentation" style="width:94%;max-width:600px;border:none;border-spacing:0;text-align:left;font-family:Arial,sans-serif;font-size:16px;line-height:22px;color:#363636;">'    
'      <tr>'
'       <td style="padding:30px;background-color:#ffffff;">'
'        <h1 style="margin-top:0;margin-bottom:16px;font-size:26px;line-height:22px;font-weight:bold;letter-spacing:-0.02em;">{new_products} New Products found!</h1>'
'        <p style="margin:0;">CL-Checker has found you {new_products} new products on Craigslist that match your search queries!</p>'
'        <br>'
'        {contents}'
'       </td>'
'      </tr>'
'      <tr>'
'       <td style="padding:10px;text-align:center;font-size:12px;background-color:#404040;color:#cccccc;">'
'        <p>{time}<br>{date}</p>'
'       </td>'
'      </tr>'
'     </table>'
'    </td>'
'   </tr>'
'  </table>'
' </div>'
'</body>'
'</html>'
)

def send_email(total_products):
    # Generate the contents
    contents = ''
    total_found = 0
    
    # Generate the contents of the email
    for i, (query, products) in enumerate(total_products.items()):
        # Create a header
        contents += f'<b>Products found for {query}:</b>'
        contents += '<ul>'
    
        # Create a list of the products
        for product in products:
            contents += f'<li><a href="{product.url}" style="color: #670067;text-decoration: underline;">{product.name}</a></li>'
            total_found += 1

        contents += '</ul>'

        # Add a separator if not the last one
        if i != len(total_products)-1:
            contents += '<br><hr><br>'

    # Get the current time
    date = datetime.datetime.now()

    # Now actually send the email
    try:
        # Login to the email
        yag = yagmail.SMTP(config.from_email, config.from_password)
        
        # Send the email
        yag.send(
            to=config.to_email,
            subject=f'CL-Checker - {total_found} new products found!',
            contents=template.format(
                new_products=total_found, 
                contents=contents,
                date=date.strftime('%B %d %Y'),
                time=date.strftime('%I:%M %p')
            ),
        )
        
    except:
        logging.error(f'Failed to send email from {config.from_email} to {config.to_email}')
        return False
    
    return True
