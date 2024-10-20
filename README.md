# Youtube Quiz Generator

This tool is used to generate short-answer quiz from youtube video url.

## Incentive

According to a number of studies, taking a short-answer quiz after learning a content reduces forgetting by %50.

## Installation

-   Install [yt-dlp](https://github.com/yt-dlp/yt-dlp) and [groq](https://groq.com/)

```bash
pip install yt-dlp
pip install groq
```

-   Get groq API key from [https://console.groq.com/keys](https://console.groq.com/keys)

-   Put yout API key into .env file

-   Ready to Go!

## Possible Improvements

-   Support for specifying number of questions
-   Better handle long videos that does not fit token limit
-   Give reference to the research paper in the README
-   Better error handling
