import functions_framework
from google import genai
from google.genai import types
import json
import csv
import io
from itertools import zip_longest

# Initialize the Generative AI client
client = genai.Client(
    vertexai=True,
    project="aihktn25-15",  # Replace with your project ID
    location="global",
)

SCHEMA = """
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "List of Advertisements",
  "description": "A JSON schema representing a list (array) of advertisements. Each advertisement in the list includes its specific type/format name and textual components.",
  "type": "array",
  "items": {
    "$ref": "#/definitions/adObject"
  },
  "definitions": {
    "adObject": {
      "title": "Advertisement Object",
      "description": "Defines the structure for a single advertisement, including its specific type/format name and textual components. An empty array for text components (headlines, body_texts, etc.) indicates that the component is not applicable for the given ad type.",
      "type": "object",
      "properties": {
        "ad_type_name": {
          "description": "The specific name or type of the ad format. This should clearly identify the ad specification being used.",
          "type": "string"
        },
        "headlines": {
          "description": "Array of headline texts. This can include short headlines or general headlines. An empty array signifies no headlines are applicable.",
          "type": "array",
          "items": {
            "type": "string",
            "description": "A single headline text."
          },
          "default": []
        },
        "long_headlines": {
          "description": "Array of long headline texts. An empty array signifies no long headlines are applicable.",
          "type": "array",
          "items": {
            "type": "string",
            "description": "A single long headline text."
          },
          "default": []
        },
        "body_texts": {
          "description": "Array of body texts. An empty array signifies no body texts are applicable.",
          "type": "array",
          "items": {
            "type": "string",
            "description": "A single body text."
          },
          "default": []
        },
        "descriptions": {
          "description": "Array of description texts. An empty array signifies no descriptions are applicable.",
          "type": "array",
          "items": {
            "type": "string",
            "description": "A single description text."
          },
          "default": []
        }
      },
      "required": [
        "ad_type_name"
      ],
      "additionalProperties": false
    }
  }
}
"""

def convert_json_ads_to_aligned_columns_csv(json_data):
    """
    Converts a list of advertisement objects from JSON format to a CSV string.
    Each row represents a single ad, with columns for each component type (headlines, etc.).
    If an ad has multiple items for a component (e.g., multiple headlines),
    they are placed in separate rows, aligned with other components using zip_longest.

    Args:
        json_data (list or str): A list of dictionaries representing the ads,
                                 or a JSON string representing such a list.

    Returns:
        str: A string containing the CSV data.
    """
    if isinstance(json_data, str):
        try:
            ads_list = json.loads(json_data)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON (for aligned_columns_csv): {e}. Ensure JSON is valid and has no comments.")
            return ""
    elif isinstance(json_data, list):
        ads_list = json_data
    else:
        print("Error (for aligned_columns_csv): json_data must be a list of dictionaries or a JSON string.")
        return ""

    if not ads_list:
        print("Warning (for aligned_columns_csv): The JSON data is empty. An empty CSV file with headers will be created.")

    fieldnames = ['ad_number', 'ad_type_name', 'headlines', 'long_headlines', 'body_texts', 'descriptions']
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction='ignore')
    writer.writeheader()
    i = 0
    for ad_object in ads_list:
        ad_type_name = ad_object.get('ad_type_name', '')
        i += 1

        headlines = ad_object.get('headlines', [])
        long_headlines = ad_object.get('long_headlines', [])
        body_texts = ad_object.get('body_texts', [])
        descriptions = ad_object.get('descriptions', [])

        # Ensure all are lists, even if None or other type in malformed JSON
        if not isinstance(headlines, list): headlines = []
        if not isinstance(long_headlines, list): long_headlines = []
        if not isinstance(body_texts, list): body_texts = []
        if not isinstance(descriptions, list): descriptions = []

        # Use zip_longest to iterate up to the length of the longest list
        # fillvalue='' ensures empty strings for shorter lists
        for h, lh, bt, d in zip_longest(headlines, long_headlines, body_texts, descriptions, fillvalue=''):
            row_data = {
                'ad_number': i,
                'ad_type_name': ad_type_name,
                'headlines': str(h) if h is not None else '',
                'long_headlines': str(lh) if lh is not None else '',
                'body_texts': str(bt) if bt is not None else '',
                'descriptions': str(d) if d is not None else ''
            }
            writer.writerow(row_data)

    return output.getvalue()


@functions_framework.http
def hello_http(request):
    """HTTP Cloud Function to generate ad specifications and return a CSV file.
    Args:
        request (flask.Request): The request object.
    Returns:
        A Flask Response object containing the CSV data.
    """
    # Set CORS headers for the preflight request
    if request.method == 'OPTIONS':
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Max-Age': '3600'
        }
        return ('', 204, headers)

    # Set CORS headers for the main request
    headers = {
        'Access-Control-Allow-Origin': '*'
    }

    data = request.form
    selected_product = data.get('selectedProduct')
    selected_platforms = data.getlist('selectedPlatforms')  # Use getlist for multiple values
    chat_input = data.get('chatInput')
    attached_files = request.files.getlist('attachedFiles')  # Use getlist for multiple files

    print("Received request:")
    print("  selectedProduct:", selected_product)
    print("  selectedPlatforms:", selected_platforms)
    print("  chatInput:", chat_input)
    print("  attachedFiles:", attached_files)

    if not selected_product or not selected_platforms or not chat_input:
        return json.dumps({"error": "Missing required parameters"}), 400, headers

    # Load specs.md content
    specs_content = ""
    try:
        # In a Cloud Function, you might need to read the file differently
        # depending on how it's deployed. Assuming it's in the same directory.
        with open("specs.md", "r") as f:
            specs_content = f.read()
    except FileNotFoundError:
        print("Warning: specs.md not found. Ad generation may be less specific.")

    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(
                    text=f"""
                    <SCHEMA>
                    {SCHEMA}
                    </SCHEMA>
                    Strictly follow the \"Guide to ad formats\". generate on {', '.join(selected_platforms)} ad by following json SCHEMA for {selected_product} based on the following prompt: {chat_input}. If guide says it has many headlines, descriptions, body texts and so on, generate maximum allowed amount according to guide.
                    """
                )
            ]
        )
    ]

    # Add specs.md content if available
    if specs_content:
        contents[0].parts.insert(0, types.Part.from_text(text=specs_content))

    # Process attached files
    for file in attached_files:
        if file.filename.endswith('.txt') or file.filename.endswith('.md'):
            file_content = file.read().decode('utf-8')
            file_context = f"Additional context from attached file '{file.filename}':\n{file_content}"
            contents[0].parts.append(types.Part.from_text(text=file_context))
        else:
            print(f"Ignoring attached file '{file.filename}'. Only text files (.txt) and Markdown files (.md) are supported.")


    model = "gemini-2.5-flash-preview-04-17"

    generate_content_config = types.GenerateContentConfig(
        temperature=0.3,
        top_p=0.95,
        max_output_tokens=8192,
        response_modalities=["TEXT"],
        safety_settings=[types.SafetySetting(
            category="HARM_CATEGORY_HATE_SPEECH",
            threshold="OFF"
        ), types.SafetySetting(
            category="HARM_CATEGORY_DANGEROUS_CONTENT",
            threshold="OFF"
        ), types.SafetySetting(
            category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
            threshold="OFF"
        ), types.SafetySetting(
            category="HARM_CATEGORY_HARASSMENT",
            threshold="OFF"
        )],
        system_instruction=[types.Part.from_text(text="""
    You are a marketing specialist and copywriter. Keep style professional.
    You will have access to ad formats guidelines, which you must follow.
    """)],
    )

    try:
        generated_content = ""
        for chunk in client.models.generate_content_stream(
                model=model,
                contents=contents,
                config=generate_content_config,
        ):
            generated_content += chunk.text

        # Remove markdown code block fences and language specifier
        cleaned_content = generated_content.replace("```json", "").replace("```", "").strip()

        # Convert the cleaned JSON string to CSV
        csv_data = convert_json_ads_to_aligned_columns_csv(cleaned_content)

        # Return the CSV data as a file
        return csv_data, 200, {'Content-Type': 'text/csv', 'Content-Disposition': 'attachment; filename="generated_ads.csv"'}

    except Exception as e:
        print(f"An error occurred during ad generation: {e}")
        return json.dumps({"error": "An error occurred during ad generation"}), 500, headers
