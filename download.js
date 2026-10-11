const https = require('https');
const fs = require('fs');

const url = 'https://raw.githubusercontent.com/Subhash9325/GeoJson-Data-of-Indian-States/master/Indian_States';
const file = fs.createWriteStream('frontend/public/india.geojson');

https.get(url, function(response) {
  if (response.statusCode === 200) {
     response.pipe(file);
     file.on('finish', function() {
       file.close();
       console.log('Download completed.');
     });
  } else {
     console.error('Failed to download: ' + response.statusCode);
  }
}).on('error', function(err) {
  fs.unlink('frontend/public/india.geojson', () => {});
  console.error('Error: ', err.message);
});
