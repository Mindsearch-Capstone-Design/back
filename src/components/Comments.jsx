import React, { useState, useEffect } from "react";
import "./Comments.css";

const Comments = () => {
  const [comments, setComments] = useState([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [selectedSentiments, setSelectedSentiments] = useState({
    긍정: true,
    중립: true,
    부정: true,
  });
  const [feedbackMenuOpen, setFeedbackMenuOpen] = useState(null);

  const commentsPerPage = 7;

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch(
          `${import.meta.env.BASE_URL}data/comments.csv`
        );
        const text = await response.text();
        const rows = text.split("\n").map((row) => row.split(","));
        const parsedComments = rows.slice(1).map((row) => ({
          date: row[0],
          content: row[1],
          link: row[2],
          sentiment:
            parseInt(row[3], 10) === 0
              ? "긍정"
              : parseInt(row[3], 10) === 1
              ? "중립"
              : "부정",
        }));
        setComments(parsedComments);
      } catch (error) {
        console.error("Error loading CSV data:", error);
      }
    };

    fetchData();
  }, []);

  // 선택된 감정에 따른 댓글 필터링
  const filteredComments = comments.filter(
    (comment) => selectedSentiments[comment.sentiment]
  );

  // 총 페이지 수 계산 (필터링된 댓글의 수에 따라 변경)
  const totalPages = Math.ceil(filteredComments.length / commentsPerPage);

  const startIndex = (currentPage - 1) * commentsPerPage;
  const displayedComments = filteredComments.slice(
    startIndex,
    startIndex + commentsPerPage
  );

  const handlePrevPage = () => {
    if (currentPage > 1) setCurrentPage(currentPage - 1);
  };

  const handleNextPage = () => {
    if (currentPage < totalPages) setCurrentPage(currentPage + 1);
  };

  const toggleFeedbackMenu = (index) => {
    setFeedbackMenuOpen(feedbackMenuOpen === index ? null : index);
  };

  const handleFeedbackSelect = (index, feedback) => {
    console.log(`Feedback for comment ${index}: ${feedback}`);
    setFeedbackMenuOpen(null);
  };

  const handleCheckboxChange = (sentiment) => {
    const selectedCount =
      Object.values(selectedSentiments).filter(Boolean).length;

    if (selectedCount === 1 && selectedSentiments[sentiment]) {
      return;
    }

    setSelectedSentiments((prev) => ({
      ...prev,
      [sentiment]: !prev[sentiment],
    }));

    setCurrentPage(1);
  };

  return (
    <div className="comments-container">
      <div className="comment-title">
        댓글 분석 결과
        <div className="comments-checkbox-panel">
          <div
            className={`comments-checkbox ${
              selectedSentiments["긍정"] ? "selected" : ""
            }`}
            onClick={() => handleCheckboxChange("긍정")}
          >
            <div className="comments-checkbox-circle positive"></div>
          </div>
          <div
            className={`comments-checkbox ${
              selectedSentiments["중립"] ? "selected" : ""
            }`}
            onClick={() => handleCheckboxChange("중립")}
          >
            <div className="comments-checkbox-circle neutral"></div>
          </div>
          <div
            className={`comments-checkbox ${
              selectedSentiments["부정"] ? "selected" : ""
            }`}
            onClick={() => handleCheckboxChange("부정")}
          >
            <div className="comments-checkbox-circle negative"></div>
          </div>
        </div>
      </div>
      <div className="comment-header">
        <div className="col">날짜</div>
        <div className="col">댓글</div>
        <div className="col">감정</div>
        <div className="col">피드백</div>
      </div>
      <div className="comment-content">
        {displayedComments.map((comment, index) => (
          <div key={index} className="comment-row">
            <div className="col">{comment.date}</div>
            <div className="col">
              <a
                href={comment.link}
                target="_blank"
                rel="noopener noreferrer"
                className="comment-link"
              >
                {comment.content}
              </a>
            </div>
            <div className="col">
              <span
                className={`sentiment-container sentiment-${comment.sentiment.toLowerCase()}`}
              >
                {comment.sentiment}
              </span>
            </div>
            <div className="col feedback-col">
              <button
                className="feedback-button"
                onClick={() => toggleFeedbackMenu(index)}
              >
                🚨
              </button>
              {feedbackMenuOpen === index && (
                <div className="feedback-dropdown">
                  <div
                    className="feedback-item"
                    onClick={() => handleFeedbackSelect(index, "긍정")}
                  >
                    긍정
                  </div>
                  <div
                    className="feedback-item"
                    onClick={() => handleFeedbackSelect(index, "중립")}
                  >
                    중립
                  </div>
                  <div
                    className="feedback-item"
                    onClick={() => handleFeedbackSelect(index, "부정")}
                  >
                    부정
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
      {totalPages >= 1 && (
        <div className="pagination">
          <button
            className="pagination-btn"
            onClick={handlePrevPage}
            disabled={currentPage === 1}
          >
            {"<"}
          </button>
          <span className="pagination-info">
            {currentPage} / {totalPages}
          </span>
          <button
            className="pagination-btn"
            onClick={handleNextPage}
            disabled={currentPage === totalPages}
          >
            {">"}
          </button>
        </div>
      )}
    </div>
  );
};

export default Comments;
