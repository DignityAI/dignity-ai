import { useState, useEffect } from 'react';

export default function ContentReview() {
  const [content, setContent] = useState([]);
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    // Fetch auto-generated content status
    fetch('/api/content-status')
      .then(res => res.json())
      .then(setContent);
  }, []);

  const filteredContent = content.filter(item => 
    filter === 'all' || item.content_type === filter
  );

  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <h3 className="text-lg font-semibold mb-4">Daily Generated Content</h3>
      
      <div className="mb-4">
        <select 
          value={filter} 
          onChange={(e) => setFilter(e.target.value)}
          className="border rounded px-3 py-2"
        >
          <option value="all">All Content</option>
          <option value="case-studies">Case Studies</option>
          <option value="power-mapping">Power Mapping</option>
          <option value="sdoh-analysis">SDOH Analysis</option>
          <option value="news-articles">News Articles</option>
          <option value="blog-posts">Blog Posts</option>
        </select>
      </div>

      <div className="space-y-3">
        {filteredContent.map(item => (
          <div key={item.id} className="border rounded p-4">
            <div className="flex justify-between items-start">
              <div>
                <h4 className="font-medium">{item.title}</h4>
                <p className="text-sm text-gray-600">{item.content_type}</p>
                <p className="text-xs text-gray-500">
                  {item.tag_count} tags • Generated {item.generation_date}
                </p>
              </div>
              <div className="flex items-center space-x-2">
                <span className={`w-3 h-3 rounded-full ${
                  item.annotated ? 'bg-green-500' : 'bg-yellow-500'
                }`}></span>
                <span className="text-xs text-gray-500">
                  {item.annotated ? 'Annotated' : 'Pending'}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
