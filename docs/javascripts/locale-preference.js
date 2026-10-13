(() => {
  const save = locale => {
    document.cookie = `bxi_locale=${locale}; Path=/; Max-Age=31536000; SameSite=Lax`;
  };
  document.addEventListener('click', event => {
    const link = event.target.closest('a[hreflang]');
    const locale = link?.getAttribute('hreflang')?.split('-')[0];
    if (locale === 'en' || locale === 'zh') save(locale);
  });

  // Explicit Chinese links stay Chinese; all other pages default to English.
  if (/^\/zh(?:\/|$)/.test(location.pathname)) return;
  const saved = document.cookie.match(/(?:^|;\s*)bxi_locale=(en|zh)(?:;|$)/)?.[1];
  let timeZone;
  try {
    timeZone = Intl.DateTimeFormat().resolvedOptions().timeZone;
  } catch {
    // Keep English when the browser cannot expose a timezone.
  }
  const chineseZones = ['Asia/Shanghai', 'Asia/Urumqi', 'Asia/Chongqing', 'Asia/Chungking', 'Asia/Harbin', 'PRC',
    'Asia/Hong_Kong', 'Hongkong', 'Asia/Macau', 'Asia/Macao', 'Asia/Taipei', 'ROC'];
  const locale = saved || (chineseZones.includes(timeZone) ? 'zh' : 'en');
  save(locale);
  if (locale === 'zh') location.replace(`/zh${location.pathname}${location.search}${location.hash}`);
})();
