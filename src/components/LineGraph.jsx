import React, { useState, useEffect } from "react";
import "./LineGraph.css";
import { ResponsiveLine } from "@nivo/line";

const LineGraph = () => {
  const [data, setData] = useState([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch(
          `${import.meta.env.BASE_URL}data/count.csv`
        );
        const text = await response.text();
        const rows = text.split("\n").map((row) => row.split(","));

        // 데이터 파싱 (2번째 행부터 시작)
        const parsedData = rows.slice(1).map((row) => ({
          date: row[0],
          positive: parseInt(row[1], 10),
          neutral: parseInt(row[2], 10),
          negative: parseInt(row[3], 10),
        }));

        // LineGraph에 필요한 형식으로 데이터 변환
        const formattedData = [
          {
            id: "긍정",
            color: "#316dec",
            data: parsedData.map((entry) => ({
              x: entry.date,
              y: entry.positive,
            })),
          },
          {
            id: "중립",
            color: "#0f9b0f",
            data: parsedData.map((entry) => ({
              x: entry.date,
              y: entry.neutral,
            })),
          },
          {
            id: "부정",
            color: "#e93434",
            data: parsedData.map((entry) => ({
              x: entry.date,
              y: entry.negative,
            })),
          },
        ];

        setData(formattedData);
      } catch (error) {
        console.error("Error loading CSV data:", error);
      }
    };

    fetchData();
  }, []);

  if (!data || data.length === 0) {
    return (
      <div className="linegraph-container no-data">
        <p className="no-data-text">Line Chart</p>
      </div>
    );
  }

  return (
    <div className="linegraph-container">
      <h3 className="linegraph-title">감정 변화 추이</h3>
      <ResponsiveLine
        data={data}
        margin={{ top: 50, right: 110, bottom: 50, left: 60 }}
        xScale={{ type: "point" }}
        yScale={{
          type: "linear",
          min: "auto",
          max: "auto",
          stacked: false,
          reverse: false,
        }}
        axisTop={null}
        axisRight={null}
        axisBottom={{
          tickSize: 5,
          tickPadding: 5,
          tickRotation: 0,
          legend: "기간",
          legendOffset: 36,
          legendPosition: "middle",
        }}
        axisLeft={{
          tickSize: 5,
          tickPadding: 5,
          tickRotation: 0,
          legend: "감정 개수",
          legendOffset: -40,
          legendPosition: "middle",
        }}
        colors={{ datum: "color" }}
        pointSize={10}
        pointColor={{ theme: "background" }}
        pointBorderWidth={2}
        pointBorderColor={{ from: "serieColor" }}
        pointLabelYOffset={-12}
        useMesh={true}
        legends={[
          {
            anchor: "bottom-right",
            direction: "column",
            justify: false,
            translateX: 120,
            translateY: -10,
            itemsSpacing: 0,
            itemDirection: "left-to-right",
            itemWidth: 80,
            itemHeight: 25,
            itemOpacity: 0.75,
            symbolSize: 12,
            symbolShape: "circle",
            symbolBorderColor: "rgba(0, 0, 0, .5)",
            effects: [
              {
                on: "hover",
                style: {
                  itemBackground: "rgba(0, 0, 0, .03)",
                  itemOpacity: 1,
                },
              },
            ],
          },
        ]}
      />
    </div>
  );
};

export default LineGraph;
