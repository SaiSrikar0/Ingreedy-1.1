from google.cloud import language_v1
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_google_nlp():
    try:
        # Initialize the client
        client = language_v1.LanguageServiceClient()
        
        # Test text
        test_text = "I have chicken, rice, and vegetables for dinner tonight"
        
        # Create document object
        document = language_v1.Document(
            content=test_text,
            type_=language_v1.Document.Type.PLAIN_TEXT
        )
        
        # Analyze entities
        response = client.analyze_entities(document=document)
        
        # Print results
        print("\nTest Results:")
        print("=" * 50)
        print(f"Input text: {test_text}")
        print("\nExtracted entities:")
        for entity in response.entities:
            print(f"- {entity.name} (Type: {entity.type_.name}, Salience: {entity.salience:.2f})")
        
        # Analyze sentiment
        sentiment_response = client.analyze_sentiment(document=document)
        sentiment = sentiment_response.document_sentiment
        print("\nSentiment Analysis:")
        print(f"Score: {sentiment.score:.2f} (Range: -1.0 to 1.0)")
        print(f"Magnitude: {sentiment.magnitude:.2f}")
        
        return True
        
    except Exception as e:
        print(f"\nError: {str(e)}")
        print("\nTroubleshooting steps:")
        print("1. Make sure you have set GOOGLE_APPLICATION_CREDENTIALS in your .env file")
        print("2. Verify that the credentials file exists at the specified path")
        print("3. Check if you have enabled the Natural Language API in your Google Cloud project")
        print("4. Ensure your Google Cloud project has billing enabled")
        return False

if __name__ == "__main__":
    print("Testing Google Cloud Natural Language API integration...")
    success = test_google_nlp()
    if success:
        print("\n✅ Test completed successfully!")
    else:
        print("\n❌ Test failed. Please check the error message above.") 