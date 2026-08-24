/**
 * ego-browser fast extraction helper with aggressive timeouts
 */

async function main() {
  let task = null;
  const results = {
    x_tweets: [],
    futu_news: []
  };

  try {
    task = await useOrCreateTaskSpace('daily-intel-brief-fast');

    // 1. Futu News (Timeout 8s)
    try {
      await openOrReuseTab('https://news.futunn.com/main', { wait: false });
      await wait(3);
      const futuData = await js(String.raw`(() => {
        const items = Array.from(document.querySelectorAll('.news-item, .item, a[href*="/post/"], .news-title')).slice(0, 10);
        return items.map(el => ({
          title: el.innerText.split('\n')[0].trim(),
          text: el.innerText.trim(),
          url: el.href || (el.closest('a') ? el.closest('a').href : '')
        })).filter(x => x.title && x.title.length > 5);
      })()`);
      if (futuData && futuData.length > 0) {
        results.futu_news = futuData;
      }
    } catch (e) {
      cliLog('Futu err: ' + e.message);
    }

    // 2. X (Twitter) (Timeout 8s)
    try {
      await openOrReuseTab('https://x.com/home', { wait: false });
      await wait(3);
      const tweets = await js(String.raw`(() => {
        const articles = Array.from(document.querySelectorAll('article[data-testid="tweet"]')).slice(0, 10);
        return articles.map(art => {
          const author = art.querySelector('[data-testid="User-Name"]')?.innerText || 'X User';
          const tweetText = art.querySelector('[data-testid="tweetText"]')?.innerText || '';
          return { author: author.split('\n')[0].trim(), text: tweetText.trim() };
        }).filter(x => x.text && x.text.length > 10);
      })()`);
      if (tweets && tweets.length > 0) {
        results.x_tweets = tweets;
      }
    } catch (e) {
      cliLog('X err: ' + e.message);
    }

  } catch (err) {
    cliLog('Global ego scrape err: ' + err.message);
  } finally {
    if (task && task.id) {
      try {
        await completeTaskSpace(task.id, { keep: false });
      } catch (e) {}
    }
  }

  cliLog('###SCRAPED_JSON_START###' + JSON.stringify(results) + '###SCRAPED_JSON_END###');
}

main().catch(err => {
  cliLog('Error in ego scraper: ' + err.message);
});
