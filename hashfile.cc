#include <fstream>
#include <cstdio>
using namespace std;

const size_t BSIZE = 0x1000;
const size_t BCNT = 0x254;

int main(int argc, char ** argv)
{
    ifstream fin(argv[1], ios::in | ios::binary);
    int res = 0;
    char buf[BSIZE];
    unsigned char * ubuf = reinterpret_cast<unsigned char *>(buf);
    while (!fin.fail())
    {
        fin.read(buf, BSIZE);
        size_t sz = BSIZE;
        if (fin.fail())
            sz = fin.gcount();
        
        for (size_t j = 0; j < sz; ++j)
        {
            int z = 3 - (j + 1) % 6;
            res += ubuf[j]*z;
        }

    }

    printf("%08x\n", res);

    return 0;
}
