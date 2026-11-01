const test = require('node:test');
const assert = require('node:assert/strict');
const {validateRecordingMetadata, recordingSampleAt} = require('../EvoRoot/EvoSpace/RecordedSession.js');
function data() {
 return {schema:'AuEvo-Recording/v1', videoFilename:'session.webm', durationMs:2000,
 telemetry:{source:'microphone', nominalSampleIntervalMs:100, summary:{sampleCount:2,averageMicrophoneLevel:.3,peakMicrophoneLevel:.4},
 timeline:[{elapsedMs:0,microphoneLevel:.2,hueDegrees:30,resonance:.1,rootValue:3},{elapsedMs:1000,microphoneLevel:.4,hueDegrees:80,resonance:.5,rootValue:6}]}};
}
test('metadata association and summary validated; timestamp lookup distinguishes gaps',()=>{
 const metadata = validateRecordingMetadata(data(),'session.webm');
 assert.equal(recordingSampleAt(metadata,100).rootValue,3);
 assert.equal(recordingSampleAt(metadata,1100).rootValue,6);
 assert.equal(recordingSampleAt(metadata,700),null);
 assert.equal(recordingSampleAt(metadata,-1),null);
 assert.equal(recordingSampleAt(metadata,2500),null);
});
test('wrong filename, bad schema, ranges, timestamps and summaries rejected',()=>{
 assert.throws(()=>validateRecordingMetadata(data(),'different.webm'));
 for(const change of [d=>d.schema='old', d=>d.durationMs=-1,d=>d.telemetry.timeline[0].microphoneLevel=NaN,
 d=>d.telemetry.timeline[0].hueDegrees=500,d=>d.telemetry.timeline[1].elapsedMs=-1,
 d=>d.telemetry.summary.sampleCount=99,d=>d.telemetry.summary.peakMicrophoneLevel=1]) {
  const d=data();change(d);assert.throws(()=>validateRecordingMetadata(d,'session.webm'));
 }
});
