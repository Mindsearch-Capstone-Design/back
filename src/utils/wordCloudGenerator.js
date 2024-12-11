import * as d3 from "d3";
import WordCloud from "wordcloud";

export const generateWordCloudData = async () => {
  try {
    const response = await fetch(
      `${import.meta.env.BASE_URL}data/comments.csv`
    );
    if (!response.ok) {
      throw new Error("Failed to load CSV file");
    }

    const text = await response.text();
    const rows = text
      .split(/\r?\n/)
      .filter((row) => row.trim() !== "")
      .map((row) => row.split(","));

    const positiveComments = [];
    const neutralComments = [];
    const negativeComments = [];

    rows.slice(1).forEach((row, index) => {
      if (row.length < 4) {
        console.warn(`Skipping invalid row ${index + 1}:`, row);
        return;
      }
      const content = row[1].trim(); // 댓글 내용
      const sentiment = row[3].trim(); // 감정 값 (0, 1, 2)

      if (sentiment === "0") {
        positiveComments.push(content);
      } else if (sentiment === "1") {
        neutralComments.push(content);
      } else if (sentiment === "2") {
        negativeComments.push(content);
      }
    });

    return {
      긍정: positiveComments.join(" "),
      중립: neutralComments.join(" "),
      부정: negativeComments.join(" "),
    };
  } catch (error) {
    console.error("Error loading CSV data:", error);
    return {
      긍정: "",
      중립: "",
      부정: "",
    };
  }
};

// 워드클라우드를 생성하여 지정된 HTML 엘리먼트에 렌더링
export const renderWordCloud = (text, element) => {
  const wordCounts = d3.rollup(
    text.split(/\s+/),
    (v) => v.length,
    (word) => word
  );

  const entries = Array.from(wordCounts).map(([word, count]) => ({
    text: word,
    size: Math.min(count * 10, 100), // 단어 크기 상한 설정
  }));

  const options = {
    list: entries.map(({ text, size }) => [text, size]),
    gridSize: 8, // 더 촘촘하게 배치
    weightFactor: (size) => size * 2,
    fontFamily: "Nanum Gothic",
    color: () => d3.schemeCategory10[Math.floor(Math.random() * 10)],
    rotateRatio: 0, // 단어 회전 비율
    backgroundColor: "#ffffff", // 배경색
    drawOutOfBound: false, // 경계 내로 제한
  };

  if (element) {
    WordCloud(element, options);
  }
};
