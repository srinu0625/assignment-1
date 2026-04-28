// =====================================================================
// ADD THIS GLOBAL VARIABLE AT THE TOP WITH OTHER STATE VARIABLES
// =====================================================================
let isLiveMode = false; // Add this line to track if we're using live data

// =====================================================================
// MODIFY THE loadLiveData FUNCTION
// =====================================================================
async function loadLiveData(){
  const key=document.getElementById('apiKey').value.trim();
  if(!key){showErr('API Key Missing','Please enter your MarketAux API key.','Get a free key at marketaux.com');return;}
  try{localStorage.setItem('marketaux_api_key',key);}catch(e){}
  apiKey=key;

  showLoading('Fetching live news from MarketAux…');setStatus('loading');
  
  // Set live mode flag
  isLiveMode = true; // Add this line

  const params=new URLSearchParams({api_token:key,symbols:CATS[currentCat].symbols,language:'en',limit:50,filter_entities:true});
  const target=`https://api.marketaux.com/v1/news/all?${params}`;
  const proxy=`https://api.allorigins.win/get?url=${encodeURIComponent(target)}`;

  try{
    const res=await fetch(proxy);
    if(!res.ok)throw new Error(`HTTP ${极速赛车开奖直播res.status}: ${res.statusText}`);
    const wrap=await res.json();
    if(!wrap.contents)throw new Error('Proxy returned empty response. API may be unreachable.');
    const data=JSON.parse(wrap.contents);

    if(data.error){
      const m=data.error.message||JSON.stringify(data.error);
      if(m.includes('invalid_api_token')||m.includes('Unauthorized'))
        showErr('Invalid API Key',m,'Check your key at marketaux.com → Account → API Tokens');
      else if(m.includes('quota')||m.includes('limit'))
        showErr('Quota Exceeded',m,'Free plan: 100 req/day. Try Demo Data or upgrade.');
      else showErr('API Error',m,'');
      setStatus('err');return;
    }

    allNews=(data.data||[]).map(normalise);
    hideErr();setStatus('live');processNews();

  }catch(err){
    showErr('Network / Parse Error',err.message,'Try Demo Data if the API is unavailable.');
    setStatus('err');
  }
}

// =====================================================================
// MODIFY THE loadDemoData FUNCTION
// =====================================================================
function loadDemoData(){
  hideErr();showLoading('Loading demo data…');
  // Set
