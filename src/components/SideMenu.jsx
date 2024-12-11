import React from "react";
import "./SideMenu.css";
import WordIcon from "./images/word.png";
import ChartIcon from "./images/chart.png";
import CommentIcon from "./images/comment.png";

const SideMenu = ({ activeButton, setActiveButton, refs }) => {
  const handleButtonClick = (buttonIndex) => {
    setActiveButton(buttonIndex);

    let targetOffset = 0;
    if (buttonIndex === 0) {
      targetOffset = refs.wordCloudRef.current.offsetTop;
    } else if (buttonIndex === 1) {
      targetOffset = refs.chartRef.current.offsetTop;
    } else if (buttonIndex === 2) {
      targetOffset = refs.commentsRef.current.offsetTop;
    }

    window.scrollTo({
      top: targetOffset - 200,
      behavior: "smooth",
    });
  };

  return (
    <div className="side-menu">
      <button
        className={`menu-button ${activeButton === 0 ? "active" : ""}`}
        onClick={() => handleButtonClick(0)}
      >
        <img src={WordIcon} alt="Word" className="menu-icon" />
      </button>
      <button
        className={`menu-button ${activeButton === 1 ? "active" : ""}`}
        onClick={() => handleButtonClick(1)}
      >
        <img src={ChartIcon} alt="Chart" className="menu-icon" />
      </button>
      <button
        className={`menu-button ${activeButton === 2 ? "active" : ""}`}
        onClick={() => handleButtonClick(2)}
      >
        <img src={CommentIcon} alt="Comment" className="menu-icon" />
      </button>
    </div>
  );
};

export default SideMenu;
