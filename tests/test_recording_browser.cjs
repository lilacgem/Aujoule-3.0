const {chromium}=require('playwright');
const fs=require('fs');
const assert=require('assert/strict');
(async()=>{
 const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH,args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 try {
 const page=await browser.newPage({acceptDownloads:true});
 const errors=[]; page.on('pageerror',e=>errors.push(e.message));
 if(process.env.THREE_JS_PATH) await page.route('https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js',r=>r.fulfill({contentType:'application/javascript',body:fs.readFileSync(process.env.THREE_JS_PATH)}));
 await page.addInitScript(()=>{
  navigator.mediaDevices.getUserMedia=async()=>{
   const ctx=new AudioContext();const osc=ctx.createOscillator();const gain=ctx.createGain();const out=ctx.createMediaStreamDestination();
   osc.frequency.value=440;gain.gain.value=.05;osc.connect(gain).connect(out);osc.start();await ctx.resume();window.testGain=gain;return out.stream;
  };
 });
 const downloads=[];page.on('download',d=>downloads.push(d));
 await page.goto(process.env.EVOSPACE_URL || 'http://127.0.0.1:8000');
 await page.waitForFunction(()=>typeof evoState!=='undefined'&&evoState);
 await page.click('#micButton');await page.waitForFunction(()=>document.querySelector('#micButton').innerText==='MIRROR CORE ENGAGED');
 await page.click('#recordButton');await page.waitForTimeout(700);
 await page.evaluate(()=>window.testGain.gain.value=.7);await page.waitForTimeout(700);
 await page.evaluate(()=>window.testGain.gain.value=0);await page.waitForTimeout(700);
 await page.click('#recordButton');await page.waitForFunction(()=>document.querySelector('#recordButton').innerText==='START RECORDING'&&!document.querySelector('#recordButton').disabled);
 await page.waitForTimeout(500);assert.equal(downloads.length,2);
 const metaDownload=downloads.find(d=>d.suggestedFilename().endsWith('.json'));
 const data=JSON.parse(fs.readFileSync(await metaDownload.path(),'utf8'));
 const video=downloads.find(d=>!d.suggestedFilename().endsWith('.json'));
 assert.equal(data.videoFilename,video.suggestedFilename());
 assert(data.telemetry.timeline.length>=6);
 const levels=data.telemetry.timeline.map(s=>s.microphoneLevel);
 assert(Math.max(...levels)>.3);assert(Math.min(...levels)<.001);
 assert(data.telemetry.timeline.every(s=>s.elapsedMs<=data.durationMs));
 assert.equal(data.telemetry.summary.peakMicrophoneLevel,Math.max(...levels));
 assert.deepEqual(data.telemetry.summary.final,data.telemetry.timeline.at(-1));
 console.log('First recording:',data.telemetry.summary.sampleCount,'samples; microphone range',Math.min(...levels),Math.max(...levels),'matched video filename.');
 await page.click('#recordButton');await page.waitForTimeout(500);await page.click('#recordButton');
 await page.waitForFunction(()=>document.querySelector('#recordButton').innerText==='START RECORDING'&&!document.querySelector('#recordButton').disabled);
 await page.waitForTimeout(500);assert.equal(downloads.length,4);
 const next=JSON.parse(fs.readFileSync(await downloads[3].path(),'utf8'));
 assert.notEqual(next.assetId,data.assetId);assert(next.durationMs<data.durationMs);
 assert(next.telemetry.timeline.every(s=>s.microphoneLevel===0));
 assert.deepEqual(errors,[]);console.log('Second recording: independent silent session; no NFT downloads or page errors.');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1)});
