import { useState } from 'react'
import './App.css'


function App() {
  const [selectedProduct, setSelectedProduct] = useState('') // State to hold the selected product
  const [selectedPlatforms, setSelectedPlatforms] = useState<string[]>([]); // State to hold selected platforms
  const [attachedFiles, setAttachedFiles] = useState<FileList | null>(null); // State to hold attached files
  const [chatInput, setChatInput] = useState(''); // State to hold chat input
  const [generatedAd, setGeneratedAd] = useState(''); // State to hold the generated ad

  const products = [
    "IntelliJ IDEA", "PyCharm", "WebStorm", "PhpStorm", "Rider", "CLion",
    "GoLand", "RubyMine", "RustRover", "DataGrip", "DataSpell", "Fleet"
  ];

  const platforms = [
    "GDN (Google Display Network)", "Search Ads (typically Google Search)", "Quora",
    "Reddit", "Facebook", "Instagram", "X (Twitter)", "LinkedIn", "YouTube", "TikTok"
  ];

  const handleProductChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedProduct(event.target.value);
    console.log("Product selected:", event.target.value);
  };

  const handlePlatformChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const platformName = event.target.value;
    if (event.target.checked) {
      setSelectedPlatforms([...selectedPlatforms, platformName]);
      console.log("Platform selected:", platformName);
    } else {
      setSelectedPlatforms(selectedPlatforms.filter(platform => platform !== platformName));
      console.log("Platform deselected:", platformName);
    }
  };

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setAttachedFiles(event.target.files);
    console.log("Files attached:", event.target.files);
  };

  const handleChatInputChange = (event: React.ChangeEvent<HTMLTextAreaElement>) => {
    setChatInput(event.target.value);
    console.log("Chat input changed:", event.target.value);
  };

  const handleSubmit = async () => {
    console.log("Submit button clicked");
    console.log("Selected Product:", selectedProduct);
    console.log("Selected Platforms:", selectedPlatforms);
    console.log("Attached Files:", attachedFiles);
    console.log("Chat Input:", chatInput);

    // Create a FormData object to send the data, including files
    const formData = new FormData();
    formData.append('selectedProduct', selectedProduct);
    selectedPlatforms.forEach(platform => formData.append('selectedPlatforms', platform));
    formData.append('chatInput', chatInput);
    if (attachedFiles) {
      for (let i = 0; i < attachedFiles.length; i++) {
        formData.append('attachedFiles', attachedFiles[i]);
      }
    }

    try {
      console.log("Sending request to backend...");
      const response = await fetch('http://188.245.180.200:9494/generate-ad', {
        method: 'POST',
        body: formData, // Use FormData for sending files
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(`Backend error: ${errorData.error}`);
      }

      // Assuming the backend now sends a file, not JSON
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'generated_ads.csv'; // Or get the filename from response headers if available
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);

      setGeneratedAd("CSV file downloaded."); // Update UI to indicate download
    } catch (error) {
      console.error("Error generating ad:", error);
      setGeneratedAd(`Error generating ad: ${error}`);
    }
  };

  return (
    <>
      <h1>AdBrains</h1>

      {/* Product Dropdown */}
      <div className="card">
        <label htmlFor="product-select">Choose a product:</label>
        <select id="product-select" value={selectedProduct} onChange={handleProductChange}>
          <option value="">--Please choose an option--</option>
          {products.map(product => (
            <option key={product} value={product}>{product}</option>
          ))}
        </select>
      </div>

      {/* Platform Checkboxes */}
      <div className="card">
        <p>Choose advertising platforms:</p>
        {platforms.map(platform => (
          <div key={platform}>
            <label htmlFor={platform}>{platform}</label>
            <input
              type="checkbox"
              id={platform}
              name="platform"
              value={platform}
              checked={selectedPlatforms.includes(platform)}
              onChange={handlePlatformChange}
            />
          </div>
        ))}
      </div>

      {/* File Attachment */}
      <div className="card">
        <label htmlFor="file-attach">Attach .txt or .md files:</label>
        <input
          type="file"
          id="file-attach"
          accept=".txt,.md"
          multiple
          onChange={handleFileChange}
        />
      </div>

      {/* Chat Input */}
      <div className="card">
        <label htmlFor="chat-input">Enter your message:</label>
        <textarea
          id="chat-input"
          rows={4}
          cols={50}
          value={chatInput}
          onChange={handleChatInputChange}
        />
      </div>

      {/* Submit Button */}
      <button onClick={handleSubmit}>Generate Ads</button>

      {/* Generated Ad Output */}
      {generatedAd && (
        <div className="card">
          <h2>Status:</h2>
          <p>{generatedAd}</p>
        </div>
      )}
    </>
  )
}

export default App