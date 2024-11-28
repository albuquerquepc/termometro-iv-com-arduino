#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <pthread.h>
#include <gtk/gtk.h>
#include <serial/serial.h>
#include <time.h>
#include <signal.h>

#define SERIAL_PORT "/dev/ttyUSB0" // Porta serial (modifique conforme necessário)
#define BAUD_RATE 9600
#define TEMPO_ATUALIZACAO 1 // Tempo em segundos
#define TAMANHO_BUFFER 256

serial::Serial arduino;
pthread_t thread_coleta;
pthread_t thread_atualizacao_grafico;
GtkWidget *entry_arquivo, *label_temperatura, *botao_iniciar, *botao_conectar;
FILE *arquivo = NULL;
int coletando_dados = 0;
time_t tempo_inicio;

void atualizar_temperatura(char *buffer)
{
    gtk_label_set_text(GTK_LABEL(label_temperatura), buffer);
}

void *coletar_dados(void *arg)
{
    char buffer[TAMANHO_BUFFER];
    FILE *arquivo_local;
    arquivo_local = fopen(gtk_entry_get_text(GTK_ENTRY(entry_arquivo)), "w");
    if (arquivo_local == NULL)
    {
        perror("Erro ao abrir arquivo");
        return NULL;
    }

    fprintf(arquivo_local, "Tempo (s), Temperatura (°C)\n");

    while (coletando_dados)
    {
        if (arduino.available())
        {
            arduino.readline(buffer, sizeof(buffer));
            time_t tempo_atual = time(NULL) - tempo_inicio;
            printf("Temperatura: %s °C\n", buffer);
            fprintf(arquivo_local, "%ld, %s\n", tempo_atual, buffer);
            atualizar_temperatura(buffer);
        }
        sleep(TEMPO_ATUALIZACAO);
    }

    fclose(arquivo_local);
    return NULL;
}

void *atualizar_grafico(void *arg)
{
    while (coletando_dados)
    {
        FILE *gnuplot = popen("gnuplot -persistent", "w");
        if (gnuplot == NULL)
        {
            perror("Erro ao abrir o gnuplot");
            return NULL;
        }
        fprintf(gnuplot, "plot 'dados.csv' using 1:2 with lines title 'Temperatura'\n");
        fclose(gnuplot);
        sleep(TEMPO_ATUALIZACAO);
    }
    return NULL;
}

void iniciar_aquisicao(GtkWidget *widget, gpointer data)
{
    const char *arquivo_path = gtk_entry_get_text(GTK_ENTRY(entry_arquivo));
    if (strlen(arquivo_path) == 0)
    {
        gtk_label_set_text(GTK_LABEL(label_temperatura), "Escolha um local para salvar");
        return;
    }

    coletando_dados = 1;
    tempo_inicio = time(NULL);
    arquivo = fopen(arquivo_path, "w");
    if (arquivo == NULL)
    {
        perror("Erro ao abrir arquivo");
        return;
    }

    gtk_button_set_label(GTK_BUTTON(botao_iniciar), "Parar");
    pthread_create(&thread_coleta, NULL, coletar_dados, NULL);
    pthread_create(&thread_atualizacao_grafico, NULL, atualizar_grafico, NULL);
}

void parar_aquisicao(GtkWidget *widget, gpointer data)
{
    coletando_dados = 0;
    gtk_button_set_label(GTK_BUTTON(botao_iniciar), "Começar");
    pthread_join(thread_coleta, NULL);
    pthread_join(thread_atualizacao_grafico, NULL);
    fclose(arquivo);
}

void conectar(GtkWidget *widget, gpointer data)
{
    try
    {
        arduino.setPort(SERIAL_PORT);
        arduino.setBaudrate(BAUD_RATE);
        arduino.open();
        printf("Conectado ao Arduino\n");
        gtk_button_set_label(GTK_BUTTON(botao_conectar), "Desconectar");
        gtk_widget_set_sensitive(botao_iniciar, TRUE);
    }
    catch (serial::IOException &e)
    {
        printf("Erro ao conectar ao Arduino: %s\n", e.what());
        gtk_label_set_text(GTK_LABEL(label_temperatura), "Erro ao conectar");
    }
}

void desconectar(GtkWidget *widget, gpointer data)
{
    arduino.close();
    gtk_button_set_label(GTK_BUTTON(botao_conectar), "Conectar");
    gtk_widget_set_sensitive(botao_iniciar, FALSE);
}

void escolher_local_arquivo(GtkWidget *widget, gpointer data)
{
    GtkWidget *dialog = gtk_file_chooser_dialog_new("Escolher Local para Salvar", NULL, GTK_FILE_CHOOSER_ACTION_SAVE, "_Cancelar", GTK_RESPONSE_CANCEL, "_Escolher", GTK_RESPONSE_ACCEPT, NULL);
    if (gtk_dialog_run(GTK_DIALOG(dialog)) == GTK_RESPONSE_ACCEPT)
    {
        char *filename = gtk_file_chooser_get_filename(GTK_FILE_CHOOSER(dialog));
        gtk_entry_set_text(GTK_ENTRY(entry_arquivo), filename);
        g_free(filename);
    }
    gtk_widget_destroy(dialog);
}

void fechar_programa(GtkWidget *widget, gpointer data)
{
    coletando_dados = 0;
    arduino.close();
    gtk_main_quit();
}

int main(int argc, char *argv[])
{
    gtk_init(&argc, &argv);

    GtkWidget *window = gtk_window_new(GTK_WINDOW_TOPLEVEL);
    gtk_window_set_title(GTK_WINDOW(window), "Monitor de Temperatura");
    g_signal_connect(window, "destroy", G_CALLBACK(fechar_programa), NULL);

    GtkWidget *box = gtk_box_new(GTK_ORIENTATION_VERTICAL, 10);
    gtk_container_add(GTK_CONTAINER(window), box);

    // Configuração da interface
    GtkWidget *botao_conectar = gtk_button_new_with_label("Conectar");
    g_signal_connect(botao_conectar, "clicked", G_CALLBACK(conectar), NULL);
    gtk_box_pack_start(GTK_BOX(box), botao_conectar, FALSE, FALSE, 0);

    GtkWidget *botao_iniciar = gtk_button_new_with_label("Começar");
    gtk_widget_set_sensitive(botao_iniciar, FALSE);
    g_signal_connect(botao_iniciar, "clicked", G_CALLBACK(iniciar_aquisicao), NULL);
    gtk_box_pack_start(GTK_BOX(box), botao_iniciar, FALSE, FALSE, 0);

    GtkWidget *label_temperatura = gtk_label_new("Temperatura: --- °C");
    gtk_box_pack_start(GTK_BOX(box), label_temperatura, FALSE, FALSE, 0);

    GtkWidget *botao_escolher_arquivo = gtk_button_new_with_label("Escolher Local para Salvar");
    g_signal_connect(botao_escolher_arquivo, "clicked", G_CALLBACK(escolher_local_arquivo), NULL);
    gtk_box_pack_start(GTK_BOX(box), botao_escolher_arquivo, FALSE, FALSE, 0);

    GtkWidget *entry_arquivo = gtk_entry_new();
    gtk_box_pack_start(GTK_BOX(box), entry_arquivo, FALSE, FALSE, 0);

    gtk_widget_show_all(window);
    gtk_main();

    return 0;
}