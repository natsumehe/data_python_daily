import pandas as pd
import fitz  # PyMuPDF
import re
from datetime import datetime  # Import datetime module

class PDFGenerator:
    def __init__(self, excel_file, template_pdf, output_folder="output_pdfs"):
        self.df = pd.read_excel(excel_file)
        self.template_pdf = template_pdf
        self.output_folder = output_folder
        self.df = self.df.drop(index=0)  # Drop the first row of the DataFrame
        self.inserted_a_ein = False

    def convert_to_string(self, value):
        """Convert datetime or other types to string"""
        if isinstance(value, pd.Timestamp):  # pandas datetime type
            return value.strftime('%Y-%m-%d')  # Or any format you prefer
        elif isinstance(value, datetime):  # If it is a Python datetime
            return value.strftime('%Y-%m-%d')  # Or any format you prefer
        else:
            return str(value)  # Return as string if it's not a datetime

    def generate_pdf(self, index, row):
        """Generate PDF for a single row of data"""
        item_a = self.convert_to_string(row['item A']) if pd.notna(row['item A']) else ""
        item_b = self.convert_to_string(row['item B']) if pd.notna(row['item B']) else ""
        item_c = self.convert_to_string(row['item C']) if pd.notna(row['item C']) else ""
        item_d = self.convert_to_string(row['item D']) if pd.notna(row['item D']) else ""
        item_1 = self.convert_to_string(row['shareholder 1']) if pd.notna(row['shareholder 1']) else ""
        item_2 = self.convert_to_string(row['shareholder 2']) if pd.notna(row['shareholder 2']) else ""
        item_3 = self.convert_to_string(row['shareholder 3']) if pd.notna(row['shareholder 3']) else ""

        # Open the PDF template
        doc = fitz.open(self.template_pdf)

        # Define the mapping of target strings and their corresponding Excel values
        search_texts = {
            "Name (see instructions)": item_a,
            "A Employer identification number": item_b,
            "B Date incorporated": item_c,
            "C State of incorporation": item_d,
            "Number, street, and room or suite no. If a P.O. box, see instructions": "17000 Red Hill Ave",
            "City or town, state or province, country, and ZIP or foreign postal code": "Irvine, CA 92614",
            "Name and title of officer or legal representative whom the IRS may call for more information": "Jay Leibowitz",
            "Telephone number of officer or legal representative": "714-845-8500",
            "Name": item_a,
            "Employer identification number": item_b,
            "Election is to be effective for tax year beginning (month, day, year) (see instructions) . . . . . . ▶": item_c,
            "reasons the election or elections were not made on time and a description of my diligent actions to correct the mistake upon its": f"{item_a}, was formed on {item_c}. We would like to request {item_a} be",
            "beginning date entered on line E) and for all": item_1,
        }

        # Step 4: Track insertion positions for specific fields
        inserted_16_y = None
        inserted_item_A_y = None

        # Step 5: Iterate through the pages of the PDF (process only pages 2 and 3)
        for page_num in range(1, 3):  # Only process page 2 (index 1) and page 3 (index 2)
            page = doc.load_page(page_num)  # Load the page

            # Get the text of the page
            page_text = page.get_text("dict")  # Get the page text in dictionary form

            # Step 6: Process each search text and insert the corresponding value
            for search_text, insert_text in search_texts.items():
                # Compile a pattern for case-sensitive matching
                pattern = re.compile(re.escape(search_text))

                # Search for the target text in the page
                text_instances = page.search_for(search_text)

                if text_instances:
                    print(f"Text '{search_text}' found on page {page_num + 1}, at positions:")

                    # Get the coordinates of the first occurrence of the text
                    target_x0, target_y1, target_x1, target_y2 = text_instances[0]

                    # Handle specific cases based on search text
                    if search_text == "A Employer identification number" and not self.inserted_a_ein:
                        insert_y = target_y1   # Adjust the Y coordinate
                        insert_x = target_x0 + 200  # Adjust the X coordinate

                        # Insert the EIN value
                        page.insert_text((insert_x, insert_y), insert_text, fontsize=8, color=(0, 0, 0))
                        print(f"Inserted EIN '{insert_text}' at position ({insert_x}, {insert_y}) on page {page_num + 1}")

                        # Set the flag to indicate EIN has been inserted
                        self.inserted_a_ein = True

                    elif search_text == "Name and title of officer or legal representative whom the IRS may call for more information":
                        insert_y = target_y1 + 30 # Keep the Y coordinate similar to the target text
                        insert_x = target_x0

                    elif search_text == "Election is to be effective for tax year beginning (month, day, year) (see instructions) . . . . . . ▶":
                        insert_y = target_y1 + 10  # Keep the Y coordinate similar to the target text
                        insert_x = target_x0 + 425  # Adjust the X coordinate

                    elif search_text == "Telephone number of officer or legal representative":
                        insert_y = target_y1 + 30
                        insert_x = target_x0  # No horizontal offset

                    elif search_text == "reasons the election or elections were not made on time and a description of my diligent actions to correct the mistake upon its":
                        insert_y = target_y1 + 45
                        insert_x = target_x0
                        inserted_item_A_y = insert_y  # Save the position of item A for later use
                        if inserted_item_A_y is not None:
                            # Insert related text below [item A]
                            insert_y_19 = inserted_item_A_y + 25
                            page.insert_text((insert_x, insert_y_19), "classified as an S-Corporation, effective {item_c}. Due to a change in management and accountants,", fontsize=8, color=(0, 0, 0))

                            insert_y_20 = inserted_item_A_y + 50
                            page.insert_text((insert_x, insert_y_20), f"{item_a} failed to obtain this requested classification as of the date of its formation. We request that you accept our late election.", fontsize=8, color=(0, 0, 0))

                            insert_y_30 = inserted_item_A_y + 75
                            page.insert_text((insert_x, insert_y_30), "filing of this IRS form 2553 Election by a Small Corporation and grant us late election relief, due to circumstances.", fontsize=8, color=(0, 0, 0))

                    elif search_text == "beginning date entered on line E) and for all":
                        insert_y = target_y1 + 65
                        insert_x = target_x0 - 100  # Offset the X coordinate
                        inserted_16_y = insert_y
                        if inserted_16_y is not None:
                            # Insert shareholder values below the "16" position
                            insert_y_17 = inserted_16_y + 60
                            page.insert_text((insert_x, insert_y_17), item_2, fontsize=8, color=(0, 0, 0))

                            # Insert shareholder 2
                            insert_y_18 = insert_y_17 + 55
                            page.insert_text((insert_x, insert_y_18), item_3, fontsize=8, color=(0, 0, 0))

                    else:
                        insert_y = target_y1 + 20
                        insert_x = target_x0  # Use the same X position

                    # Insert the text into the PDF at the found coordinates
                    page.insert_text((insert_x, insert_y), insert_text, fontsize=8, color=(0, 0, 0))
                    print(f"Inserted text '{insert_text}' at position ({insert_x}, {insert_y}) on page {page_num + 1}")

                else:
                    print(f"Text '{search_text}' not found on page {page_num + 1}.")

        # Save the modified PDF with the filename based on item A
        output_pdf_path = f"{item_a}_output.pdf"  # Use item A as the filename
        doc.save(output_pdf_path)

        print(f"PDF for row {index + 1} saved as '{output_pdf_path}'.")

    def generate_all_pdfs(self):
        """Generate PDFs for all rows in the DataFrame"""
        for index, row in self.df.iterrows():
            self.generate_pdf(index, row)

# Usage example
pdf_generator = PDFGenerator("test_python_edited.xlsx", "f2553.pdf")
pdf_generator.generate_all_pdfs()
