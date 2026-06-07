const int piezoLeft = A2;   
const int piezoRight = A0;  
const int piezoTop = A1;    

const int noiseFloor = 30; // Solid threshold to keep the system dead silent when at rest

void setup() {
  Serial.begin(115200); 
  analogReference(INTERNAL); // 1.1V Internal reference for maximum precision range
}

void loop() {
  int valLeft  = analogRead(piezoLeft);
  int valRight = analogRead(piezoRight);
  int valTop   = analogRead(piezoTop);

  // Trigger when a genuine vibration wave enters the matrix
  if (valLeft > noiseFloor || valRight > noiseFloor || valTop > noiseFloor) {
    
    unsigned long windowStart = micros();
    int peakLeft = valLeft;
    int peakRight = valRight;
    int peakTop = valTop;

    // 2-millisecond snapshot to capture the highest structural peaks
    while (micros() - windowStart < 2000) {
      int rL = analogRead(piezoLeft);
      int rR = analogRead(piezoRight);
      int rT = analogRead(piezoTop);

      if (rL > peakLeft)  peakLeft = rL;
      if (rR > peakRight) peakRight = rR;
      if (rT > peakTop)   peakTop = rT;
    }

    int totalIntensity = peakLeft + peakRight + peakTop;

    if (totalIntensity > 0) {
      // Calculate clean ratio distributions (-1000 to 1000)
      float relX = (float)(peakRight - peakLeft) / totalIntensity;
      float relY = (float)(peakTop - ((peakLeft + peakRight) / 2)) / totalIntensity;

      int outX = (int)(relX * 1000);
      int outY = (int)(relY * 1000);

      // Send the raw balanced calculations to Python
      Serial.print(outX);
      Serial.print(",");
      Serial.println(outY);
    }

    // Crucial cooldown delay to let the $20\times20\text{ cm}$ metal plate completely stop ringing
    delay(220); 
  }
}