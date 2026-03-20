#include <time.h>
#include <stdio.h>
clock_t  start, stop; /* clock_t 是处理器时间（滴答数）的内置类型 */
double   duration;    /* 记录某函数的运行时间（单位：秒） */

int main ( )
{

    /* clock() 返回程序开始运行以来已消耗的
       处理器时间（滴答数） */
    //    int i = 0;
    // start = clock(); 
    // for(i = 0; i < 1000000; i++)   /* 记录函数调用开始时的滴答数 */
    // {
    // };

    // // function();         /* 在此处调用你的函数 */
    // stop = clock();     /* 记录函数调用结束时的滴答数 */
    // duration = ((double)(stop - start))/CLK_TCK;
    // /* CLK_TCK 是内置常量，等于每秒的滴答数 */
    printf("函数运行时间：%f 秒\n", 1.0);

    return 0;
}
