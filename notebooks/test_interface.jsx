import React, { useState } from 'react';
import { Upload, Trash2, ChevronLeft, ChevronRight, Download } from 'lucide-react';

const ReviewClassifier = () => {
  const [reviews, setReviews] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [fileName, setFileName] = useState('');
  const [hasChanges, setHasChanges] = useState(false);

  const categories = ['pet', 'child', 'handicap'];

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    try {
      const text = await file.text();
      const lines = text.split('\n').filter(line => line.trim());
      const headers = lines[0].split(',').map(h => h.trim().replace(/['"]/g, ''));

      const reviewIndex = headers.findIndex(
        h => h.toLowerCase() === 'reviews' || h.toLowerCase() === 'review'
      );
      const categoryIndex = headers.findIndex(
        h => h.toLowerCase() === 'category' || h.toLowerCase() === 'categorie'
      );

      if (reviewIndex === -1) {
        alert('Colonne "reviews" non trouvée dans le CSV');
        return;
      }

      const data = lines.slice(1).map((line, idx) => {
        const values = line
          .match(/(".*?"|[^",\s]+)(?=\s*,|\s*$)/g)
          ?.map(v => v.trim().replace(/^["']|["']$/g, '')) || [];
        return {
          id: idx,
          review: values[reviewIndex] || '',
          category: categoryIndex !== -1 ? values[categoryIndex] : '',
          deleted: false
        };
      }).filter(item => item.review);

      setReviews(data);
      setCurrentIndex(0);
      setFileName(file.name);
      setHasChanges(false);
    } catch (error) {
      alert('Erreur lors de la lecture du fichier: ' + error.message);
    }
  };

  const currentReview = reviews.length > 0 ? reviews[currentIndex] : null;
  const activeReviews = reviews.filter(r => !r.deleted);
  const currentPos = activeReviews.findIndex(r => r.id === currentReview?.id) + 1;

  const changeCategory = (newCategory) => {
    const updated = [...reviews];
    if (!updated[currentIndex].deleted) {
      updated[currentIndex].category = newCategory;
    }
    setReviews(updated);
    setHasChanges(true);
  };

  const deleteReview = () => {
    const updated = [...reviews];
    updated[currentIndex].deleted = true;
    setReviews(updated);
    setHasChanges(true);

    // Aller à la review suivante active, sinon à la précédente
    const nextActiveIndex = updated.findIndex((r, idx) => idx > currentIndex && !r.deleted);
    if (nextActiveIndex !== -1) {
      setCurrentIndex(nextActiveIndex);
    } else {
      const prevActiveIndex = [...updated.slice(0, currentIndex)]
        .reverse()
        .findIndex(r => !r.deleted);
      if (prevActiveIndex !== -1) {
        setCurrentIndex(currentIndex - prevActiveIndex - 1);
      } else {
        setCurrentIndex(0);
      }
    }
  };

  const navigateReview = (direction) => {
    if (direction === 'next') {
      const nextIndex = reviews.findIndex((r, idx) => idx > currentIndex && !r.deleted);
      if (nextIndex !== -1) setCurrentIndex(nextIndex);
    } else {
      const prevIndex = reviews.slice(0, currentIndex).reverse().findIndex(r => !r.deleted);
      if (prevIndex !== -1) setCurrentIndex(currentIndex - prevIndex - 1);
    }
  };

  const downloadCSV = () => {
    const activeData = reviews.filter(r => !r.deleted);
    const headers = 'reviews,category';
    const rows = activeData.map(r => `"${r.review.replace(/"/g, '""')}","${r.category}"`);
    const csv = [headers, ...rows].join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = (fileName?.endsWith('.csv')
      ? fileName.replace('.csv', '_modified.csv')
      : 'reviews_modified.csv');
    a.click();
    URL.revokeObjectURL(url);
    setHasChanges(false);
  };

  // --- Cas où aucun fichier n’est encore chargé ---
  if (reviews.length === 0) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
        <div className="bg-white rounded-xl shadow-lg p-8 max-w-md w-full">
          <h1 className="text-2xl font-bold text-gray-800 mb-6 text-center">
            Classification de Reviews
          </h1>
          <label className="flex flex-col items-center justify-center w-full h-48 border-2 border-dashed border-indigo-300 rounded-lg cursor-pointer hover:border-indigo-500 hover:bg-indigo-50 transition">
            <Upload className="w-12 h-12 text-indigo-400 mb-3" />
            <span className="text-sm text-gray-600 font-medium">Charger un fichier CSV</span>
            <span className="text-xs text-gray-400 mt-1">Colonnes : reviews, category</span>
            <input
              type="file"
              accept=".csv"
              onChange={handleFileUpload}
              className="hidden"
            />
          </label>
        </div>
      </div>
    );
  }

  // --- Cas où toutes les reviews sont supprimées ---
  if (!currentReview || currentReview.deleted || activeReviews.length === 0) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <p className="text-gray-600 text-lg">Toutes les reviews ont été supprimées.</p>
      </div>
    );
  }

  // --- Interface principale ---
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
      <div className="max-w-4xl mx-auto">
        <div className="bg-white rounded-xl shadow-lg p-6 mb-4">
          <div className="flex items-center justify-between mb-4">
            <h1 className="text-2xl font-bold text-gray-800">Classification de Reviews</h1>
            {hasChanges && (
              <button
                onClick={downloadCSV}
                className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition"
              >
                <Download className="w-4 h-4" />
                Télécharger CSV
              </button>
            )}
          </div>

          <div className="flex items-center justify-between text-sm text-gray-600">
            <span>{fileName}</span>
            <span>{currentPos} / {activeReviews.length} reviews</span>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-lg p-6">
          <div className="mb-6">
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-lg font-semibold text-gray-700">Review</h2>
              <span
                className={`px-3 py-1 rounded-full text-sm font-medium ${
                  currentReview.category === 'pet'
                    ? 'bg-purple-100 text-purple-700'
                    : currentReview.category === 'child'
                    ? 'bg-blue-100 text-blue-700'
                    : currentReview.category === 'handicap'
                    ? 'bg-orange-100 text-orange-700'
                    : 'bg-gray-100 text-gray-700'
                }`}
              >
                {currentReview.category || 'Non catégorisé'}
              </span>
            </div>
            <div className="bg-gray-50 rounded-lg p-4 border border-gray-200 min-h-32">
              <p className="text-gray-800 leading-relaxed">{currentReview.review}</p>
            </div>
          </div>

          <div className="space-y-3">
            <h3 className="text-sm font-semibold text-gray-700 mb-2">Changer la catégorie :</h3>
            <div className="grid grid-cols-3 gap-3">
              {categories.map(cat => (
                <button
                  key={cat}
                  onClick={() => changeCategory(cat)}
                  className={`py-3 px-4 rounded-lg font-medium transition ${
                    currentReview.category === cat
                      ? 'bg-indigo-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {cat.charAt(0).toUpperCase() + cat.slice(1)}
                </button>
              ))}
            </div>

            <button
              onClick={deleteReview}
              className="w-full flex items-center justify-center gap-2 py-3 px-4 bg-red-600 text-white rounded-lg hover:bg-red-700 transition font-medium"
            >
              <Trash2 className="w-4 h-4" />
              Supprimer cette review
            </button>
          </div>

          <div className="flex items-center justify-between mt-6 pt-6 border-t border-gray-200">
            <button
              onClick={() => navigateReview('prev')}
              disabled={currentIndex === 0 || !reviews.slice(0, currentIndex).some(r => !r.deleted === true)}
              className="flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ChevronLeft className="w-4 h-4" />
              Précédent
            </button>
            <button
              onClick={() => navigateReview('next')}
              disabled={!reviews.slice(currentIndex + 1).some(r => !r.deleted)}
              className="flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Suivant
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ReviewClassifier;
