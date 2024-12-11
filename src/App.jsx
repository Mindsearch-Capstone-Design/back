import React, { useState, useEffect, useRef } from "react";
import Header from "./components/Header";
import SideMenu from "./components/SideMenu";
import DefaultImage from "./components/images/default-img.png";
import WordCloudRank from "./components/WordCloudRank";
import PieChart from "./components/PieChart";
import LineGraph from "./components/LineGraph";
import Comments from "./components/Comments";
import "./App.css";

function App() {
  const [lineGraphData, setLineGraphData] = useState([]);
  const [selectedEmotion, setSelectedEmotion] = useState("긍정");
  const [hasData, setHasData] = useState(false);
  const [activeButton, setActiveButton] = useState(0);

  // Refs for each section
  const wordCloudRef = useRef(null);
  const chartRef = useRef(null);
  const commentsRef = useRef(null);

  useEffect(() => {
    const handleScroll = () => {
      const scrollPosition = window.scrollY;
      const wordCloudPosition = wordCloudRef.current.offsetTop;
      const chartPosition = chartRef.current.offsetTop;
      const commentsPosition = commentsRef.current.offsetTop;

      const chartHeight = chartRef.current.offsetHeight;

      if (
        scrollPosition >= wordCloudPosition &&
        scrollPosition < chartPosition - chartHeight / 1.2
      ) {
        setActiveButton(0);
      } else if (
        scrollPosition >= chartPosition - chartHeight / 2 &&
        scrollPosition < commentsPosition - chartHeight / 2
      ) {
        setActiveButton(1);
      } else if (scrollPosition >= commentsPosition - chartHeight / 2) {
        setActiveButton(2);
      }
    };

    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const handleSearch = (startDate, endDate) => {
    setHasData(true);
    setActiveButton(0); // Default active button

    const positive = [10, 20, 15, 25];
    const neutral = [15, 10, 20, 30];
    const negative = [5, 10, 5, 10];

    const start = startDate ? new Date(startDate) : new Date("2024-01-01");
    const end = endDate ? new Date(endDate) : new Date("2024-12-01");
    const interval = Math.floor((end - start) / 3);

    const period = Array.from({ length: 4 }, (_, i) => {
      const date = new Date(start.getTime() + interval * i);
      return date.toISOString().split("T")[0];
    });

    const data = [
      {
        id: "긍정",
        color: "#0000FF",
        data: period.map((p, index) => ({ x: p, y: positive[index] })),
      },
      {
        id: "중립",
        color: "#008000",
        data: period.map((p, index) => ({ x: p, y: neutral[index] })),
      },
      {
        id: "부정",
        color: "#FF0000",
        data: period.map((p, index) => ({ x: p, y: negative[index] })),
      },
    ];

    setLineGraphData(data);
  };

  return (
    <div className="App">
      <Header
        onSearch={(startDate, endDate) => handleSearch(startDate, endDate)}
      />
      <SideMenu
        activeButton={activeButton}
        setActiveButton={setActiveButton}
        refs={{ wordCloudRef, chartRef, commentsRef }}
      />
      {!hasData ? (
        <div className="default-view">
          <img src={DefaultImage} alt="Default" className="default-img" />
          <p className="default-text">데이터가 없습니다.</p>
        </div>
      ) : (
        <div className="grid-container">
          <div className="wordcloud-rank" ref={wordCloudRef}>
            <WordCloudRank
              selectedEmotion={selectedEmotion}
              setSelectedEmotion={setSelectedEmotion}
              hasData={hasData}
            />
          </div>
          <div className="charts-container" ref={chartRef}>
            <div className="pie-chart">
              <PieChart hasData={hasData} />
            </div>
            <div className="line-graph">
              <LineGraph data={lineGraphData} />
            </div>
          </div>
          <div className="comments-section" ref={commentsRef}>
            <Comments />
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
