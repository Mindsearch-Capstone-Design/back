import React, { useState, useEffect } from "react";
import WordCloud from "./WordCloud";
import Rank from "./Rank";
import { generateWordCloudData } from "../utils/wordCloudGenerator";
import "./WordCloudRank.css";

const WordCloudRank = ({ hasData }) => {
  const [selectedSentiment, setSelectedSentiment] = useState("긍정");
  const [wordCloudData, setWordCloudData] = useState("");
  const [keywords, setKeywords] = useState([]);

  useEffect(() => {
    const fetchData = async () => {
      const data = await generateWordCloudData();
      if (data && selectedSentiment) {
        const sentimentText = data[selectedSentiment] || "";
        setWordCloudData(sentimentText);

        // 키워드와 빈도 계산
        const wordCounts = sentimentText.split(/\s+/).reduce((acc, word) => {
          acc[word] = (acc[word] || 0) + 1;
          return acc;
        }, {});

        // 상위 5개 키워드 추출
        const sortedKeywords = Object.entries(wordCounts)
          .sort(([, a], [, b]) => b - a)
          .slice(0, 5)
          .map(([word, count]) => ({ word, count }));

        setKeywords(sortedKeywords);
      }
    };

    fetchData();
  }, [selectedSentiment]);

  return (
    <div className="wordcloud-rank-wrapper">
      <div className="wordcloud-content">
        <div className="checkbox-container">
          <input
            type="radio"
            id="positive"
            name="sentiment"
            value="긍정"
            checked={selectedSentiment === "긍정"}
            onChange={() => setSelectedSentiment("긍정")}
          />
          <label htmlFor="positive" className="positive-circle"></label>
          <input
            type="radio"
            id="neutral"
            name="sentiment"
            value="중립"
            checked={selectedSentiment === "중립"}
            onChange={() => setSelectedSentiment("중립")}
          />
          <label htmlFor="neutral" className="neutral-circle"></label>
          <input
            type="radio"
            id="negative"
            name="sentiment"
            value="부정"
            checked={selectedSentiment === "부정"}
            onChange={() => setSelectedSentiment("부정")}
          />
          <label htmlFor="negative" className="negative-circle"></label>
        </div>
        <h2 className="wordcloud-title">워드클라우드</h2>
        <WordCloud
          title={selectedSentiment}
          data={wordCloudData}
          hasData={hasData && wordCloudData && wordCloudData.length > 0}
          size="large"
        />
      </div>
      <div className="rank-content">
        <h2 className="rank-title">키워드 순위</h2>
        <Rank selectedSentiment={selectedSentiment} keywords={keywords} />
      </div>
    </div>
  );
};

export default WordCloudRank;
