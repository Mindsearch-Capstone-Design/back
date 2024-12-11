import React, { useEffect, useState } from "react";
import "./PieChart.css";
import { ResponsivePie } from "@nivo/pie";

const PieChart = ({ hasData }) => {
  const [data, setData] = useState([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch(
          `${import.meta.env.BASE_URL}data/ratio.csv`
        );
        const text = await response.text();
        const rows = text.split("\n").map((row) => row.split(","));

        // Extract relevant ratios (5th column)
        const positiveRatio = parseFloat(rows[1][0]);
        const neutralRatio = parseFloat(rows[2][0]);
        const negativeRatio = parseFloat(rows[3][0]);

        setData([
          { id: "긍정", label: "긍정", value: positiveRatio, color: "#316dec" },
          { id: "중립", label: "중립", value: neutralRatio, color: "#0f9b0f" },
          { id: "부정", label: "부정", value: negativeRatio, color: "#e93434" },
        ]);
      } catch (error) {
        console.error("Error loading CSV data:", error);
      }
    };

    fetchData();
  }, []);

  if (!hasData) {
    return (
      <div className="circlechart-container no-data">
        <p className="no-data-text">Pie Chart</p>
      </div>
    );
  }

  return (
    <div className="circlechart-container">
      <h2 className="piechart-title">감정 비율</h2>
      <ResponsivePie
        data={data}
        margin={{ top: 40, right: 80, bottom: 80, left: 80 }}
        innerRadius={0.5}
        padAngle={0.7}
        cornerRadius={3}
        activeOuterRadiusOffset={8}
        borderWidth={1}
        borderColor={{
          from: "color",
          modifiers: [["darker", 0.2]],
        }}
        colors={{ datum: "data.color" }}
        arcLinkLabelsSkipAngle={10}
        arcLinkLabelsTextColor="#333333"
        arcLinkLabelsThickness={2}
        arcLinkLabelsColor={{ from: "color" }}
        arcLabelsSkipAngle={10}
        arcLabelsTextColor={{
          from: "color",
          modifiers: [["darker", 2]],
        }}
        legends={[
          {
            anchor: "bottom",
            direction: "row",
            justify: false,
            translateX: 0,
            translateY: 40,
            itemsSpacing: 0,
            itemWidth: 100,
            itemHeight: 18,
            itemTextColor: "#999",
            itemDirection: "top-to-bottom",
            itemOpacity: 1,
            symbolSize: 18,
            symbolShape: "circle",
            effects: [
              {
                on: "hover",
                style: {
                  itemTextColor: "#000",
                },
              },
            ],
          },
        ]}
      />
    </div>
  );
};

export default PieChart;
