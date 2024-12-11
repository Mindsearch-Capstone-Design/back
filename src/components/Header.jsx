import React, { useState } from "react";
import "./Header.css";
import HeaderLogo from "./images/TeamLogo.png";
import InstagramLogo from "./images/instagram.png";
import YoutubeLogo from "./images/youtube.png";
import FacebookLogo from "./images/facebook.png"; // 페이스북 로고 추가
import SearchIcon from "./images/search.png";

const Header = ({ onSearch }) => {
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [keyword, setKeyword] = useState("");
  const [platform, setPlatform] = useState("");

  const handleSearch = () => {
    if (!startDate || !endDate) {
      alert("기간을 설정하세요");
      return;
    }
    if (keyword.trim().length < 2) {
      alert("검색어는 두 글자 이상으로 입력하세요");
      return;
    }
    if (!platform) {
      alert("플랫폼을 선택하세요");
      return;
    }
    onSearch(startDate, endDate, platform, keyword); // 플랫폼 및 키워드 추가 전달
  };

  const handleEnterPress = (e) => {
    if (e.key === "Enter") {
      handleSearch();
    }
  };

  const refreshPage = () => {
    window.location.reload();
  };

  return (
    <div className="header-container">
      <img
        src={HeaderLogo}
        alt="Team Logo"
        className="header-logo"
        onClick={refreshPage}
      />
      <div className="header-content">
        <div className="search-period">
          <input
            type="date"
            id="start-date"
            className={`date-select ${startDate ? "date-active" : ""}`}
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
          />
          ~
          <input
            type="date"
            id="end-date"
            className={`date-select ${endDate ? "date-active" : ""}`}
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
          />
        </div>
        <div className="platform-select">
          <div className="custom-dropdown">
            <button
              className={`dropdown-button ${!platform ? "placeholder" : ""}`}
            >
              {platform ? (
                <>
                  <img
                    src={
                      platform === "youtube"
                        ? YoutubeLogo
                        : platform === "instagram"
                        ? InstagramLogo
                        : FacebookLogo
                    }
                    alt={platform}
                    className="dropdown-selected-icon"
                  />
                  {platform === "youtube"
                    ? "유튜브"
                    : platform === "instagram"
                    ? "인스타그램"
                    : "페이스북"}
                </>
              ) : (
                "플랫폼"
              )}
            </button>
            <div className="dropdown-menu">
              <div
                className="dropdown-item"
                onClick={() => setPlatform("youtube")}
              >
                <img
                  src={YoutubeLogo}
                  alt="YouTube Logo"
                  className="dropdown-icon"
                />
                유튜브
              </div>
              <div
                className="dropdown-item"
                onClick={() => setPlatform("instagram")}
              >
                <img
                  src={InstagramLogo}
                  alt="Instagram Logo"
                  className="dropdown-icon"
                />
                인스타그램
              </div>
              <div
                className="dropdown-item"
                onClick={() => setPlatform("facebook")}
              >
                <img
                  src={FacebookLogo}
                  alt="Facebook Logo"
                  className="dropdown-icon"
                />
                페이스북
              </div>
            </div>
          </div>
        </div>
        <div className="search-input">
          <input
            type="text"
            placeholder="Search"
            className={`input-height ${
              keyword.trim() !== "" ? "input-active" : ""
            }`}
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            onKeyDown={handleEnterPress}
          />
          <button className="input-button" onClick={handleSearch}>
            <img src={SearchIcon} alt="Search Icon" className="search-icon" />
          </button>
        </div>
      </div>
    </div>
  );
};

export default Header;
