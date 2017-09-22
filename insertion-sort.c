// C program for insertion sort
#include <stdio.h>
#include <math.h>

int comps = 0;

/* Function to sort an array using insertion sort*/
void insertionSort(int arr[], int n)
{
   int i, key, j;
   for (i = 1; i < n; i++)
   {
       key = arr[i];
       j = i-1;
 
       /* Move elements of arr[0..i-1], that are
          greater than key, to one position ahead
          of their current position */
       while (j >= 0 && arr[j] > key)
       {
           comps ++;
           arr[j+1] = arr[j];
           j = j-1;
       }
       arr[j+1] = key;
   }
}
 
// A utility function ot print an array of size n
void printArray(int arr[], int n)
{
   int i;
   for (i=0; i < n; i++)
       printf("%d ", arr[i]);
   printf("\n");
}
 
 
 
/* Driver program to test insertion sort */
int main(int argc, char * argv[])
{
    FILE * in = fopen(argv[1], "r");
    int i = 0;
    int sortarray[20];
    char c; 

    while (i < 20 && ((c = fgetc(in)) != EOF)) {
       sortarray[i]= (int) c;
       i++;
    } 

    fclose(in);
 
    insertionSort(sortarray, 20);
    printArray(sortarray, 20);
    printf("comps: %d\n", comps);

    if (comps == 190) {
       return 1;
    }
    return 0;
}
