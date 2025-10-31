"use client";

import { useState, useRef, useEffect } from "react";
import { submitSnap } from "../lib/api";

interface QuickListingModalProps {
  isOpen: boolean;
  onClose: () => void;
}

type Step = 1 | 2 | 3;

interface ListingFormData {
  title: string;
  description: string;
  price: string;
  condition: string;
  category: string;
  photoFile: File | null;
}

export function QuickListingModal({ isOpen, onClose }: QuickListingModalProps) {
  const [currentStep, setCurrentStep] = useState<Step>(1);
  const [formData, setFormData] = useState<ListingFormData>({
    title: "",
    description: "",
    price: "0.00",
    condition: "used-good",
    category: "electronics",
    photoFile: null,
  });

  const [photoFileName, setPhotoFileName] = useState<string>("");
  const [isAnalyzingPhoto, setIsAnalyzingPhoto] = useState(false);
  const [isFetchingPrice, setIsFetchingPrice] = useState(false);
  const [isPosting, setIsPosting] = useState(false);
  const [postMessage, setPostMessage] = useState<{
    type: "success" | "error";
    text: string;
  } | null>(null);

  const [marketplaces, setMarketplaces] = useState({
    ebay: true,
    facebook: true,
    offerup: true,
  });

  const photoInputRef = useRef<HTMLInputElement>(null);
  const dropzoneRef = useRef<HTMLDivElement>(null);

  // Photo upload handler
  const handlePhotoUpload = async (file: File) => {
    setPhotoFileName(file.name);
    setFormData((prev) => ({ ...prev, photoFile: file }));
    setIsAnalyzingPhoto(true);

    // Mock AI analysis - in production, this would call your backend
    await new Promise((resolve) => setTimeout(resolve, 2500));

    // Mock results
    const mockTitle = "Apple AirPods Pro 2nd Generation (A Grade, Used)";
    const mockDescription =
      "Perfectly functioning second-generation AirPods Pro. Comes with original case, charging cable, and three sizes of ear tips. Excellent condition, minimal signs of wear. Ready to ship immediately!";

    setFormData((prev) => ({
      ...prev,
      title: mockTitle,
      description: mockDescription,
    }));
    setIsAnalyzingPhoto(false);
  };

  const handlePhotoInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.[0]) {
      handlePhotoUpload(e.target.files[0]);
    }
  };

  // Drag and drop handlers
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (dropzoneRef.current) {
      dropzoneRef.current.classList.add("border-indigo-500", "bg-indigo-50");
    }
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (dropzoneRef.current) {
      dropzoneRef.current.classList.remove("border-indigo-500", "bg-indigo-50");
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (dropzoneRef.current) {
      dropzoneRef.current.classList.remove("border-indigo-500", "bg-indigo-50");
    }
    if (e.dataTransfer.files?.[0]) {
      handlePhotoUpload(e.dataTransfer.files[0]);
    }
  };

  // Step 2: Fetch AI price
  const handleFetchPrice = async () => {
    setIsFetchingPrice(true);
    // Mock price fetch - in production, call your backend
    await new Promise((resolve) => setTimeout(resolve, 1500));

    const basePrice = 150;
    const conditionFactor =
      formData.condition === "new"
        ? 1.5
        : formData.condition === "like-new"
          ? 1.2
          : 1.0;
    let recommendedPrice = basePrice * conditionFactor;
    recommendedPrice = Math.round(recommendedPrice / 5) * 5;

    setFormData((prev) => ({
      ...prev,
      price: recommendedPrice.toFixed(2),
    }));
    setIsFetchingPrice(false);
  };

  // Validation
  const isStep1Valid = () => {
    return formData.photoFile && formData.title.trim().length > 0;
  };

  const isStep3Valid = () => {
    return (
      Object.values(marketplaces).some((v) => v) &&
      formData.title.trim().length > 0 &&
      parseFloat(formData.price) > 0
    );
  };

  // Navigate steps
  const goToStep = async (step: Step) => {
    if (step === 2 && !isStep1Valid()) {
      return;
    }
    if (step === 2 && currentStep === 1) {
      await handleFetchPrice();
    }
    setCurrentStep(step);
  };

  // Post listing
  const handlePostListing = async () => {
    if (!isStep3Valid()) {
      setPostMessage({
        type: "error",
        text: "Please fill in all required fields and select at least one marketplace.",
      });
      return;
    }

    setIsPosting(true);
    setPostMessage(null);

    try {
      const selectedMarketplaces = Object.entries(marketplaces)
        .filter(([, selected]) => selected)
        .map(([name]) => name);

      // Encode photo
      if (!formData.photoFile) {
        throw new Error("No photo selected");
      }

      const arrayBuffer = await formData.photoFile.arrayBuffer();
      const bytes = new Uint8Array(arrayBuffer);
      let binary = "";
      for (let i = 0; i < bytes.byteLength; i += 1) {
        binary += String.fromCharCode(bytes[i]);
      }
      const encodedPhoto = btoa(binary);

      // Submit snap job
      const response = await submitSnap({
        photos: [encodedPhoto],
        notes: `Title: ${formData.title}\nDescription: ${formData.description}\nPrice: $${formData.price}\nCondition: ${formData.condition}`,
        source: selectedMarketplaces.join(","),
      });

      setPostMessage({
        type: "success",
        text: `Success! Your item has been posted to ${selectedMarketplaces.length} channel(s): ${selectedMarketplaces.join(", ")}. Job ID: ${response.job_id}`,
      });

      // Reset form
      setTimeout(() => {
        resetForm();
        onClose();
      }, 2000);
    } catch (error) {
      setPostMessage({
        type: "error",
        text:
          error instanceof Error
            ? error.message
            : "Failed to post listing. Please try again.",
      });
    } finally {
      setIsPosting(false);
    }
  };

  const resetForm = () => {
    setFormData({
      title: "",
      description: "",
      price: "0.00",
      condition: "used-good",
      category: "electronics",
      photoFile: null,
    });
    setPhotoFileName("");
    setCurrentStep(1);
    setPostMessage(null);
  };

  if (!isOpen) return null;

  const marketplaceCount = Object.values(marketplaces).filter((v) => v).length;
  const stepTitles = [
    "Upload Photo",
    "Pricing & Details",
    "Cross-Post",
  ];

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
      <div className="w-full max-w-lg bg-white rounded-2xl shadow-xl overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-indigo-600 to-indigo-700 px-6 py-4 text-white">
          <h1 className="text-3xl font-extrabold">List an Item Fast</h1>
          <p className="text-sm font-medium text-indigo-100 mt-1">
            Step {currentStep} of 3: {stepTitles[currentStep - 1]}
          </p>
        </div>

        <div className="p-6 md:p-8">
          {/* Step 1: Photo & AI Details */}
          {currentStep === 1 && (
            <div className="space-y-6">
              {/* Image Upload */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Item Photo (Tap to Upload)
                </label>
                <div
                  ref={dropzoneRef}
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                  onDrop={handleDrop}
                  onClick={() => photoInputRef.current?.click()}
                  className="flex justify-center items-center w-full h-40 border-2 border-dashed border-gray-300 rounded-xl cursor-pointer hover:border-indigo-500 hover:bg-indigo-50 transition-colors duration-150 relative"
                >
                  <input
                    ref={photoInputRef}
                    type="file"
                    accept="image/*"
                    className="absolute inset-0 opacity-0 cursor-pointer"
                    onChange={handlePhotoInputChange}
                  />
                  <div className="text-center">
                    <svg
                      className="mx-auto h-8 w-8 text-gray-400"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 18m-5 3H4a2 2 0 01-2-2v-7a2 2 0 012-2h16a2 2 0 012 2v7a2 2 0 01-2 2h-1c-.538 0-1.042-.211-1.414-.586l-1.586-1.586a2 2 0 00-2.828 0L9.586 16.586A2 2 0 008.172 17H7z"
                      />
                    </svg>
                    <p className="mt-1 text-sm text-gray-600">
                      Drag & drop or click
                    </p>
                    {photoFileName && (
                      <p className="text-xs text-indigo-600 mt-1 font-medium">
                        {photoFileName}
                      </p>
                    )}
                  </div>
                </div>
              </div>

              {/* AI Title */}
              <div>
                <label className="block text-sm font-bold text-gray-700 mb-1">
                  AI-Generated Title (Confirm or Edit)
                </label>
                {isAnalyzingPhoto && (
                  <div className="text-center p-3 border border-indigo-200 rounded-lg bg-indigo-50">
                    <svg
                      className="animate-spin h-5 w-5 text-indigo-600 mx-auto"
                      xmlns="http://www.w3.org/2000/svg"
                      fill="none"
                      viewBox="0 0 24 24"
                    >
                      <circle
                        className="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="4"
                      />
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                      />
                    </svg>
                    <p className="text-sm text-indigo-600 mt-1">
                      Analyzing image for details...
                    </p>
                  </div>
                )}
                <input
                  type="text"
                  value={formData.title}
                  onChange={(e) =>
                    setFormData((prev) => ({ ...prev, title: e.target.value }))
                  }
                  disabled={isAnalyzingPhoto}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-indigo-500 focus:border-indigo-500 transition-colors disabled:bg-gray-100"
                  placeholder="Upload a photo to generate title..."
                />
              </div>

              {/* AI Description */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  AI-Generated Description
                </label>
                <textarea
                  rows={4}
                  value={formData.description}
                  onChange={(e) =>
                    setFormData((prev) => ({
                      ...prev,
                      description: e.target.value,
                    }))
                  }
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-indigo-500 focus:border-indigo-500 transition-colors"
                  placeholder="Detailed description generated from image analysis will appear here."
                />
              </div>
            </div>
          )}

          {/* Step 2: Pricing & Details */}
          {currentStep === 2 && (
            <div className="space-y-6">
              {/* AI Price Recommendation */}
              <div className="bg-indigo-50 p-4 rounded-xl border border-indigo-200">
                <p className="text-xs font-bold text-indigo-700 uppercase mb-1 flex items-center">
                  <svg
                    className="w-4 h-4 mr-1"
                    fill="currentColor"
                    viewBox="0 0 20 20"
                  >
                    <path
                      fillRule="evenodd"
                      d="M10 18a8 8 0 100-16 8 8 0 000 16zm-1-9a1 1 0 001 1h.01a1 1 0 100-2H10a1 1 0 00-1 1zm0 4a1 1 0 102 0 1 1 0 00-2 0z"
                      clipRule="evenodd"
                    />
                  </svg>
                  AI Price Recommendation
                </p>
                <p className="text-2xl font-bold text-indigo-800">
                  {isFetchingPrice
                    ? "Analyzing..."
                    : `$${formData.price} - $${(parseFloat(formData.price) + 10).toFixed(2)}`}
                </p>
                <p className="text-xs text-indigo-600 mt-1">
                  Based on comps from eBay, Facebook, and Offerup.
                </p>
              </div>

              {/* Price Input */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Your Price ($)
                </label>
                <input
                  type="number"
                  value={formData.price}
                  onChange={(e) =>
                    setFormData((prev) => ({ ...prev, price: e.target.value }))
                  }
                  disabled={isFetchingPrice}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-indigo-500 focus:border-indigo-500 transition-colors font-mono text-lg"
                  step="0.01"
                  min="0"
                />
              </div>

              {/* Condition */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Condition
                </label>
                <select
                  value={formData.condition}
                  onChange={(e) =>
                    setFormData((prev) => ({
                      ...prev,
                      condition: e.target.value,
                    }))
                  }
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-indigo-500 focus:border-indigo-500 transition-colors"
                >
                  <option value="new">New</option>
                  <option value="like-new">Like New</option>
                  <option value="used-good">Used (Good)</option>
                  <option value="used-fair">Used (Fair)</option>
                  <option value="for-parts">For Parts</option>
                </select>
              </div>

              {/* Category */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Category (Auto-Detected)
                </label>
                <select
                  value={formData.category}
                  onChange={(e) =>
                    setFormData((prev) => ({
                      ...prev,
                      category: e.target.value,
                    }))
                  }
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-indigo-500 focus:border-indigo-500 transition-colors"
                >
                  <option value="electronics">Electronics &gt; Headphones</option>
                  <option value="fashion">Fashion &gt; Accessories</option>
                  <option value="home">Home & Garden</option>
                  <option value="other">Other</option>
                </select>
              </div>
            </div>
          )}

          {/* Step 3: Marketplace Selection */}
          {currentStep === 3 && (
            <div className="space-y-6">
              <h2 className="text-xl font-bold text-gray-800">
                Select Where to Post
              </h2>

              {/* Marketplace Checkboxes */}
              <div className="space-y-4">
                {[
                  { id: "ebay", label: "eBay", initials: "E" },
                  {
                    id: "facebook",
                    label: "Facebook Marketplace",
                    initials: "f",
                  },
                  { id: "offerup", label: "OfferUp (Local)", initials: "O" },
                ].map((marketplace) => (
                  <div
                    key={marketplace.id}
                    className="flex items-center justify-between p-3 border border-gray-200 rounded-xl bg-gray-50"
                  >
                    <label className="flex items-center text-sm font-medium text-gray-700 cursor-pointer flex-1">
                      <div
                        className={`w-6 h-6 mr-3 rounded text-white font-bold flex items-center justify-center text-xs ${
                          marketplace.id === "ebay"
                            ? "bg-gray-800"
                            : marketplace.id === "facebook"
                              ? "bg-blue-600"
                              : "bg-black"
                        }`}
                      >
                        {marketplace.initials}
                      </div>
                      {marketplace.label}
                    </label>
                    <input
                      type="checkbox"
                      checked={
                        marketplaces[
                          marketplace.id as keyof typeof marketplaces
                        ]
                      }
                      onChange={(e) =>
                        setMarketplaces((prev) => ({
                          ...prev,
                          [marketplace.id]: e.target.checked,
                        }))
                      }
                      className="h-4 w-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
                    />
                  </div>
                ))}
              </div>

              {/* Post Message */}
              {postMessage && (
                <div
                  className={`p-4 rounded-xl ${
                    postMessage.type === "success"
                      ? "bg-green-100 text-green-800"
                      : "bg-red-100 text-red-800"
                  }`}
                >
                  {postMessage.text}
                </div>
              )}

              {isPosting && (
                <div className="text-center">
                  <svg
                    className="animate-spin h-5 w-5 text-indigo-600 mx-auto"
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    />
                  </svg>
                  <p className="text-sm text-indigo-600 mt-2">
                    Cross-Posting in progress...
                  </p>
                </div>
              )}
            </div>
          )}

          {/* Navigation Buttons */}
          <div className="flex gap-4 mt-8">
            {currentStep > 1 && (
              <button
                onClick={() => goToStep((currentStep - 1) as Step)}
                disabled={isPosting}
                className="flex-1 py-3 px-4 border border-gray-300 rounded-xl shadow-md text-gray-700 bg-white hover:bg-gray-100 transition-colors font-semibold disabled:opacity-60"
              >
                Back
              </button>
            )}
            {currentStep < 3 && (
              <button
                onClick={() => goToStep((currentStep + 1) as Step)}
                disabled={!isStep1Valid() || isAnalyzingPhoto}
                className="flex-1 py-3 px-4 border border-transparent rounded-xl shadow-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-colors font-semibold disabled:bg-indigo-300"
              >
                Next: {currentStep === 1 ? "Get AI Price" : "Select Channels"}
              </button>
            )}
            {currentStep === 3 && (
              <button
                onClick={handlePostListing}
                disabled={isPosting || !isStep3Valid()}
                className={`flex-1 py-3 px-4 border border-transparent rounded-xl shadow-md text-white transition-colors font-semibold disabled:opacity-60 ${
                  marketplaceCount > 0
                    ? "bg-green-600 hover:bg-green-700"
                    : "bg-gray-400"
                }`}
              >
                Post to {marketplaceCount} {marketplaceCount === 1 ? "Channel" : "Channels"}
              </button>
            )}
          </div>
        </div>

        {/* Close Button */}
        {currentStep === 1 && !isAnalyzingPhoto && !isPosting && (
          <button
            onClick={onClose}
            className="absolute top-4 right-4 text-gray-500 hover:text-gray-700"
          >
            <svg
              className="w-6 h-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        )}
      </div>
    </div>
  );
}
