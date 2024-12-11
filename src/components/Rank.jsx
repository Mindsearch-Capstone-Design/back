import React from "react";
import "./Rank.css";

const Rank = ({ selectedSentiment, keywords }) => {
  const getBackgroundColor = () => {
    if (selectedSentiment === "긍정") {
      return "rgb(186, 227, 255)";
    } else if (selectedSentiment === "중립") {
      return "rgb(164, 255, 144)";
    } else if (selectedSentiment === "부정") {
      return "rgb(255, 231, 243)";
    }
    return "transparent";
  };

  return (
    <div className="rank-container">
      <ul className="rank-list">
        {keywords.map((keyword, index) => (
          <li
            key={index}
            className="rank-word"
            style={{ backgroundColor: getBackgroundColor() }}
          >
            {index + 1}위: {keyword.word} ({keyword.count}회)
          </li>
        ))}
      </ul>
    </div>
  );
};

export default Rank;
