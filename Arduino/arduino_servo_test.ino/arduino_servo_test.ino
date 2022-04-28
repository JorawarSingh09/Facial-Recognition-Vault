#include <Servo.h>

Servo myservo; // create servo object to control a servo
// twelve servo objects can be created on most boards

int pos = 20; // variable to store the servo position, 20 is when lock is disengageed

void setup()
{
    myservo.attach(9); // attaches the servo on pin 9 to the servo object
    myservo.write(pos);
}

void loop()
{
    for (pos = 20; pos <= 180; pos += 1)
    { // goes from 0 degrees to 180 degrees, lock engaged
        // in steps of 1 degree
        myservo.write(pos); // tell servo to go to position in variable 'pos'
        delay(15);          // waits 15ms for the servo to reach the position
    }
    delay(10000);
    for (pos = 180; pos >= 20; pos -= 1)
    {                       // goes from 180 degrees to 0 degrees
        myservo.write(pos); // tell servo to go to position in variable 'pos'
        delay(15);          // waits 15ms for the servo to reach the position
    }
    delay(1000);
}
