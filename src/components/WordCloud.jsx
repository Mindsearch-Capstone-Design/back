import React, { useEffect, useRef } from "react";
import "./WordCloud.css";
import { renderWordCloud } from "../utils/wordCloudGenerator";

const WordCloud = ({ data, hasData, size }) => {
  const wordCloudRef = useRef(null);

  useEffect(() => {
    console.log("WordCloud Data:", data);
    if (hasData && data && wordCloudRef.current) {
      renderWordCloud(data, wordCloudRef.current);
    }
  }, [data, hasData]);

  if (!hasData || !data || data.length === 0) {
    return (
      <div
        className={`wordcloud-container no-data ${
          size === "large" ? "large" : ""
        }`}
      >
        <p className="no-data-text">WordCloud</p>
      </div>
    );
  }

  return (
    <div className="wordcloud-wrapper">
      <div
        className={`wordcloud-container ${size === "large" ? "large" : ""}`}
        ref={wordCloudRef} // DOM 참조 전달
        style={{ width: "100%", height: "400px" }} // 크기 설정
      ></div>
    </div>
  );
};

export default WordCloud;
