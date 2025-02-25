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
 - Ensure previous responses are chronological
 - Add ability to ask questions of historical data