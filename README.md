### Pull S&P 500 Heat Map

Currently:  
 - Pulls from tradingview.com
   - Uses javascript to set to dark mode
   - Scales image by 50%
   - Saves to sp500_heatmap.png
  - Sends image to chatgpt for analysis
  - Includes previous analysis, if it exists
  - Sends results via email
  - Formats response markdown - not happy with yet

To-Do:
 - Fix markdown rendering
 - Improve the prompt, a lot
 - Add response request for judgement on priority of notification
 - Create browser for response history
 - Improve previous analysis inclusion
   - Find way to compress that won't lose useful information
   - Find a way to include particularly important past maps in the request?
   - Completely drop uneventful periods. Ie. 'Include 4 past analysis' = Include 4 past _significant_ analysis
 - Add function to include links to ticker details and adds other response embelishments
 - Add ability to ask questions of historical data

---

## Possible one-off prompt, where there is no past analysis

### Instructions:

Analyze the current S&P 500 Heat Map that is attached.

1. Identify current points of interest:
   - Highlight stocks and sectors with notable movements.
   - Consider both absolute performance (biggest gainers/losers) and relative
     movements (e.g., defensive stocks rising while growth stocks decline).

2. Assign an Importance Score (1-10) for each point of interest:
   - 10: Major market-moving event, likely to have lasting impact.
   - 7-9: Strong movement, potential emerging trend.
   - 4-6: Noticeable but uncertain impact.
   - 1-3: Routine fluctuation, likely noise.

3. Ensure the response is structured for future analysis:
   - Summarize market conditions clearly for easier trend tracking.
   - Keep formatting consistent.

---

## Possible prompt with past analysis

### Instructions:

Analyze the current S&P 500 Heat Map and compare it to past market conditions. You 
do not have access to past images—only the previous LLM-generated analysis. 
Identify new points of interest, track ongoing trends, and highlight significant 
changes. Ensure the response is structured for easy future analysis.

1. Compare current market conditions to past analysis:
   - Determine if previous points of interest have strengthened, weakened, or reversed.
   - Identify new emerging movements not present before.
   - Look for sector rotations, divergences, or sustained trends.
   
2. Identify current points of interest:
   - Highlight stocks and sectors with notable movements.
   - Consider both absolute performance (biggest gainers/losers) and relative 
movements (e.g., defensive stocks rising while growth stocks decline).

3. Assign an Importance Score (1-10) for each point of interest:
   - 10: Major market-moving event, likely to have lasting impact.
   - 7-9: Strong movement, potential emerging trend.
   - 4-6: Noticeable but uncertain impact.
   - 1-3: Routine fluctuation, likely noise.

4. Ensure the response is structured for future analysis:
   - Summarize market conditions clearly for easier trend tracking.
   - Keep formatting consistent.

Previous Analysis:
(Insert prior LLM response here.)

---

## Constrained Response

```json
{
  "when": "<Current Date & Time>",
  "points_of_interest": [
    {
       /* one of sector of stocks is expected, but neither required */
      "sector": "<Sector Name>",
      "stocks": ["<Stock Ticker>", "<Stock Ticker>"],
      "observation": "<Key movement or trend>",
      "interest_type": "<Enum>",
      "importance": <1-10>
    }
  ],
  "trend_summary": "<Overall summary of changes.>"
}
```

## Interest Types
Each type intended to be distinct, with an emphasis on clear identification, and
be specific to heat-map analysis.    
Must be a added to prompt.

📊 Broad Market Trend – Major indices or most sectors moving in the same direction.  
🔄 Sector Rotation – Funds shifting between sectors (e.g., growth vs. value).  
⚖️ Divergence – Some sectors moving opposite to the broader market.  
🔥 Momentum Cluster – A group of stocks (by sector or industry) showing strong momentum.  
🛑 Reversal Signal – Previously strong/weak sectors suddenly shifting direction.  
💰 Capital Concentration – Large-cap stocks (e.g., MAG7) dominating movement.  
📉 Extreme Weakness – A sector or large group of stocks heavily declining.  
📈 Breakout Strength – A sector or industry showing consistent gains.  
⚡ Volatility Surge – Highly mixed movements within a sector or market-wide.  
📰 News-Driven Shift – A clear reaction to an external event (earnings, Fed, geopolitical).  
💵 Rate-Sensitive Moves – Stocks/sectors responding to interest rate expectations.  
🌍 Global Influence – Foreign market trends visibly impacting the heat map.  
>>>>>>> f473223 (WIP)
