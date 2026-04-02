/*
 * =====================================================================================
 *
 *       Filename:  sphere_math.c
 *
 *    Description:  Simple calculator to find the area, surface area, and volume of a sphere!
 *
 *        Version:  1.0
 *        Created:  04/02/2026 12:24:45 PM
 *       Revision:  none
 *       Compiler:  gcc
 *
 *      Author(s):  BransonBailey (Branson Bailey),
 *   Organization:
 *
 * =====================================================================================
 */
#include <math.h>
#include <stdio.h>
#include <stdlib.h>

int main() {
  double radius = 0.0;
  double area = 0.0;
  const double PI = 3.14159;
  double surfaceArea = 0.0;
  double volume = 0.0;

  printf("Enter the radius: ");
  scanf("%lf", &radius);

  area = PI * pow(radius, 2);
  surfaceArea = 4 * PI * pow(radius, 2);
  volume = (4.0 / 3.0) * PI * pow(radius, 3);
  printf("Area: %.2lf\n", area);
  printf("Surface Area: %.2lf\n", surfaceArea);
  printf("Volume: %.2lf\n", volume);
  return 0;
}
